"""Telegram bot channel (D44) against real PostgreSQL with a mock Bot API transport.

`local-substitute` evidence: the poller, inbox worker, dispatcher and adapter run for real, but
Telegram is an in-process `httpx.MockTransport`. These tests prove the contract (private-chat
and allowlist rules, persist-before-confirm offsets, deduplication, media limits, single
submission, failure classes, exact PDF bytes, no token in logs). They do NOT prove Telegram
accepts these requests or that a phone receives anything; those steps are in docs/MORNING_ACTIONS.md.
"""

import json
import logging

import httpx
import psycopg
import pytest
from luma.core.config import settings
from luma.features.messaging import telegram_client
from luma.features.messaging.inbound import GREETING
from luma.features.messaging.telegram_ingress import poll_once, reduce_update
from luma_agent.runtime.delivery import deliver_one
from test_manual_workflow import make_draft, post
from test_voice_intake import wav_bytes
from test_whatsapp import drain, outbox, queue_reply, rows

TOKEN = "123456789:telegram-bot-token-for-tests"
USER = "987654321"


class Bot:
    """Recording mock of the Bot API and its file host."""

    def __init__(self):
        """Start with an empty update queue and healthy send/file defaults."""
        self.requests = []
        self.updates = []
        self.next_message = 100
        self.send_error = None
        self.poll_error = None
        self.fail_answer = False
        self.file = {"file_id": "x", "file_unique_id": "u", "file_size": 100, "file_path": "voice/file_1.oga"}
        self.file_bytes = b""

    def handler(self, request: httpx.Request) -> httpx.Response:
        """Answer one request and remember it."""
        self.requests.append(request)
        method = request.url.path.rsplit("/", 1)[-1]
        if request.url.path.startswith(f"/file/bot{TOKEN}/"):
            return httpx.Response(200, content=self.file_bytes)
        if method == "getUpdates":
            if self.poll_error:
                raise self.poll_error
            offset = json.loads(request.content).get("offset")
            pending = [u for u in self.updates if offset is None or u["update_id"] >= offset]
            return httpx.Response(200, json={"ok": True, "result": pending})
        if method in ("sendMessage", "sendDocument"):
            if self.send_error:
                if isinstance(self.send_error, Exception):
                    raise self.send_error
                return self.send_error
            self.next_message += 1
            return httpx.Response(200, json={"ok": True, "result": {"message_id": self.next_message}})
        if method == "answerCallbackQuery":
            if self.fail_answer:
                return httpx.Response(400, json={"ok": False, "error_code": 400})
            return httpx.Response(200, json={"ok": True, "result": True})
        if method == "getFile":
            return httpx.Response(200, json={"ok": True, "result": self.file})
        return httpx.Response(404, json={"ok": False, "error_code": 404})

    def calls(self, method):
        """Return requests for one Bot API method."""
        return [r for r in self.requests if r.url.path.endswith(f"/{method}")]


@pytest.fixture
def bot(environment, monkeypatch):
    """Configure the Telegram channel for the isolated company and route Bot API calls to the mock."""
    fake = Bot()
    values = {
        "TELEGRAM_BOT_TOKEN": TOKEN,
        "TELEGRAM_COMPANY_ID": str(environment["company"]),
        "TELEGRAM_ALLOWED_USERS": USER,
        "ENABLE_LIVE_TELEGRAM": "true",
        "ENABLE_PAID_AI": "false",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    settings.cache_clear()
    monkeypatch.setattr(
        telegram_client,
        "make_client",
        lambda timeout=telegram_client.TIMEOUT: httpx.Client(transport=httpx.MockTransport(fake.handler)),
    )
    return fake


def update(update_id, *, user=USER, chat=None, chat_type="private", message_id=None, **content):
    """Build one Telegram Update carrying a message from `user`."""
    return {
        "update_id": update_id,
        "message": {
            "message_id": message_id or update_id,
            "date": 1_700_000_000,
            "from": {"id": int(user), "is_bot": False, "first_name": "Synthetic", "last_name": "Customer"},
            "chat": {"id": int(chat or user), "type": chat_type},
            **content,
        },
    }


def telegram_conversation(env):
    """Return the Telegram conversation created for the test user."""
    [row] = rows(env, "select * from luma.conversations where company_id=%s and channel='telegram'", env["company"])
    return row


def start(env, bot_):
    """Receive one allowlisted text and return its conversation id with opening work blocked."""
    bot_.updates = [update(1, text="Please quote 3 DL-001.")]
    assert poll_once(None, timeout=0) == 2
    drain()
    cid = str(telegram_conversation(env)["id"])
    with psycopg.connect(env["dsn"]) as conn:
        conn.execute("update luma.outbox set status='blocked' where conversation_id=%s", (cid,))
    return cid


def test_only_private_human_chats_reduce_to_events():
    """Groups, bots, mismatched chat ids and non-message updates are skipped; media picks the right fields."""
    assert reduce_update(update(1, chat_type="group", chat="-100", text="hi")) is None
    assert reduce_update(update(1, chat="111", text="hi")) is None
    robot = update(1, text="hi")
    robot["message"]["from"]["is_bot"] = True
    assert reduce_update(robot) is None
    assert reduce_update({"update_id": 1, "edited_message": {}}) is None
    identity, kind, event = reduce_update(update(5, text="hello"))
    assert (identity, kind, event["type"], event["text"], event["channel"]) == (
        f"tg:{USER}:5",
        "message",
        "text",
        "hello",
        "telegram",
    )
    voice = reduce_update(update(6, voice={"file_id": "voice_file_id_1", "duration": 2, "mime_type": "audio/ogg"}))[2]
    assert (voice["type"], voice["media_id"], voice["mime"]) == ("audio", "voice_file_id_1", "audio/ogg")
    sizes = [
        {"file_id": "small_photo_id", "width": 90, "height": 90},
        {"file_id": "large_photo_id", "width": 1280, "height": 960},
        {"file_id": "medium_photo_id", "width": 320, "height": 240},
    ]
    photo = reduce_update(update(7, photo=sizes))[2]
    assert (photo["type"], photo["media_id"], photo["mime"]) == ("image", "large_photo_id", "image/jpeg")
    assert reduce_update(update(8, sticker={"file_id": "s"}))[2]["type"] == "unsupported"


def test_updates_are_stored_before_the_offset_confirms_them(environment, bot):
    """Offsets advance only after storage; a failed poll keeps the offset; repeats are stored once."""
    bot.updates = [update(10, text="first"), update(11, text="second")]
    assert poll_once(None, timeout=0) == 12
    assert poll_once(None, timeout=0) == 12  # unconfirmed redelivery is deduplicated
    count = rows(environment, "select count(*) n from luma.inbox where company_id=%s", environment["company"])
    assert count[0]["n"] == 2
    bot.poll_error = httpx.ConnectError("down")
    assert poll_once(12, timeout=0) == 12
    assert json.loads(bot.calls("getUpdates")[0].content)["allowed_updates"] == ["message", "callback_query"]


def test_allowlisted_user_opens_a_telegram_conversation_and_others_are_ignored(environment, bot):
    """An allowlisted user's text creates a Telegram conversation; an unknown user creates nothing."""
    bot.updates = [update(1, user="555", text="hi")]
    poll_once(None, timeout=0)
    drain()
    assert rows(environment, "select 1 from luma.conversations where company_id=%s", environment["company"]) == []
    cid = start(environment, bot)
    convo = telegram_conversation(environment)
    assert (convo["recipient"], convo["customer_name"]) == (USER, "Synthetic Customer")
    [message] = rows(environment, "select * from luma.messages where conversation_id=%s and actor='customer'", cid)
    assert message["provider_id"] == f"tg:{USER}:1"


def test_start_command_queues_one_greeting_and_no_agent_work(environment, bot):
    """/start opens the conversation and queues the fixed greeting instead of a customer request."""
    bot.updates = [update(1, text="/start")]
    poll_once(None, timeout=0)
    drain()
    cid = telegram_conversation(environment)["id"]
    [notice] = outbox(environment, cid)
    assert notice["payload"]["text"] == GREETING
    assert rows(environment, "select 1 from luma.messages where conversation_id=%s and actor='customer'", cid) == []


def test_voice_note_is_downloaded_within_limits_and_enters_the_media_pipeline(environment, bot):
    """getFile then a bounded download stores the voice note and queues transcription."""
    bot.file_bytes = wav_bytes()
    bot.file = {**bot.file, "file_size": len(bot.file_bytes)}
    bot.updates = [update(1, voice={"file_id": "voice_file_id_1", "duration": 2, "mime_type": "audio/wav"})]
    poll_once(None, timeout=0)
    drain()
    cid = telegram_conversation(environment)["id"]
    [stored] = rows(environment, "select * from luma.media where conversation_id=%s", cid)
    environment["files"].append(stored["original_path"])
    assert stored["kind"] == "audio"
    assert [j["kind"] for j in rows(environment, "select kind from luma.jobs where conversation_id=%s", cid)] == [
        "transcribe"
    ]


@pytest.mark.parametrize(
    "file",
    [
        {"file_id": "x", "file_unique_id": "u", "file_size": 50 * 1024 * 1024, "file_path": "voice/a.oga"},
        {"file_id": "x", "file_unique_id": "u", "file_size": 10, "file_path": "../../etc/passwd"},
    ],
    ids=["declared-too-large", "path-traversal"],
)
def test_hostile_file_metadata_is_refused_without_downloading(environment, bot, file):
    """An oversize declared file or a suspicious path is refused before any download."""
    bot.file = file
    bot.updates = [update(1, voice={"file_id": "voice_file_id_1", "duration": 2, "mime_type": "audio/ogg"})]
    poll_once(None, timeout=0)
    drain()
    assert rows(environment, "select 1 from luma.media where company_id=%s", environment["company"]) == []
    assert not [r for r in bot.requests if "/file/bot" in r.url.path]


def test_text_reply_is_sent_once_without_a_service_window(environment, bot):
    """A reply posts one sendMessage, even 3 days after the last customer message, and records its id."""
    cid = start(environment, bot)
    with psycopg.connect(environment["dsn"]) as conn:
        conn.execute("update luma.conversations set last_customer_at=now()-interval '3 days' where id=%s", (cid,))
    queue_reply(environment, cid)
    assert deliver_one(environment["company"]) is True
    assert deliver_one(environment["company"]) is False
    [request] = bot.calls("sendMessage")
    assert json.loads(request.content) == {"chat_id": int(USER), "text": "Which colour temperature?"}
    [row] = [r for r in outbox(environment, cid) if r["status"] != "blocked"]
    assert row["status"] == "submitted" and row["provider_id"] == f"tg:{USER}:101"


@pytest.mark.parametrize(
    ("failure", "status", "code"),
    [
        (httpx.Response(403, json={"ok": False, "error_code": 403}), "failed", "telegram_403"),
        (httpx.Response(429, json={"ok": False, "error_code": 429, "parameters": {"retry_after": 3}}), "failed", "telegram_429"),
        (httpx.ReadTimeout("slow"), "unknown", "transport_error"),
        (httpx.Response(502, text="bad gateway"), "unknown", "http_502"),
        (httpx.Response(200, json={"ok": True, "result": {}}), "unknown", "no_message_id"),
        (httpx.ConnectError("down"), "failed", "connect_error"),
    ],
    ids=["blocked-by-user", "flood", "timeout", "server-error", "no-id", "unreachable"],
)
def test_uncertain_and_failed_sends_are_never_retried(environment, bot, failure, status, code):
    """Definite refusals are `failed`, uncertain outcomes `unknown`, and only one attempt is made."""
    cid = start(environment, bot)
    queue_reply(environment, cid)
    bot.send_error = failure
    assert deliver_one(environment["company"]) is True
    assert deliver_one(environment["company"]) is False
    assert len(bot.calls("sendMessage")) == 1
    [row] = [r for r in outbox(environment, cid) if r["status"] != "blocked"]
    assert (row["status"], row["error_code"], row["provider_id"]) == (status, code, None)


def test_gates_block_without_calling_telegram(environment, bot, monkeypatch):
    """Live mode off or a recipient removed from the allowlist blocks before any send."""
    cid = start(environment, bot)
    for env_key, value in (("ENABLE_LIVE_TELEGRAM", "false"), ("TELEGRAM_ALLOWED_USERS", "111")):
        monkeypatch.setenv(env_key, value)
        settings.cache_clear()
        queue_reply(environment, cid, f"gate {env_key}")
        deliver_one(environment["company"])
        monkeypatch.setenv("ENABLE_LIVE_TELEGRAM", "true")
        monkeypatch.setenv("TELEGRAM_ALLOWED_USERS", USER)
        settings.cache_clear()
    codes = [r["error_code"] for r in outbox(environment, cid) if r["payload"].get("text", "").startswith("gate")]
    assert codes == ["live_adapter_not_enabled", "recipient_not_allowed"]
    assert bot.calls("sendMessage") == []


def test_approved_quotation_is_uploaded_as_the_exact_canonical_pdf(environment, bot):
    """sendDocument carries the stored PDF bytes unchanged with the staff-approved caption."""
    cid = start(environment, bot)
    with psycopg.connect(environment["dsn"]) as conn:
        conn.execute(
            "update luma.snapshots set source='google_sheets',observed_at=now() where company_id=%s",
            (environment["company"],),
        )
    quote = make_draft(environment, cid)
    environment["files"].append(f"{environment['company']}/quotes/{quote['id']}.pdf")
    decision = post(environment, f"/conversations/{cid}/decision", {"expected_revision": 1, "decision": "approve"})
    assert decision.status_code == 200
    with psycopg.connect(environment["dsn"]) as conn:
        conn.execute("update luma.snapshots set observed_at=now() where company_id=%s", (environment["company"],))
    deliver_one(environment["company"])
    [upload] = bot.calls("sendDocument")
    staff_pdf = environment["api"].get(f"/api/quotes/{quote['id']}/pdf", headers=environment["headers"]).content
    assert staff_pdf in upload.content and b"Total USD" in upload.content
    [row] = [r for r in outbox(environment, cid) if r["kind"] == "quotation"]
    assert row["status"] == "submitted" and row["provider_id"].startswith(f"tg:{USER}:")


def test_bot_token_never_reaches_logs(environment, bot, caplog):
    """Failed polls and sends log only opaque codes; the token-bearing URL is never logged."""
    caplog.set_level(logging.DEBUG)
    bot.updates = [update(1, text="hi")]
    poll_once(None, timeout=0)  # a successful request is where httpx would log the URL at INFO
    bot.poll_error = httpx.ReadTimeout(f"timeout for https://api.telegram.org/bot{TOKEN}/getUpdates")
    poll_once(None, timeout=0)
    assert "Telegram poll failed: transport_error" in caplog.text
    assert TOKEN not in caplog.text and TOKEN.split(":")[1] not in caplog.text
