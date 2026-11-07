/**
 * Gmail channel (decision D47). Two one-minute triggers:
 * - pollLumaMail pushes new mails under the LumaQuote label to the signed gateway; the cursor moves
 *   only after the backend has stored them. The account's own messages (our replies) are skipped.
 * - sendLumaMail claims replies the backend queued, sends each once from Gmail and reports the result.
 * Customer content is never logged; only HTTP status codes are kept in Script Properties.
 */

var MAIL_BATCH = 5;
var MAIL_BODY_CHARS = 8000;
var MAIL_FIRST_RUN_MS = 60 * 60 * 1000;
/**
 * How long a one-minute trigger waits for the shared script lock (shared by every .gs file). The supplier
 * sync can hold it for ~10 s; a 1 s try-lock made send/poll skip silently every minute. A timeout now
 * throws, so the run shows as Failed instead of Completed.
 */
var LOCK_WAIT_MS = 25000;

/** Return the Gmail label name that marks customer requests (Script Property LUMA_GMAIL_LABEL, default LumaQuote). */
function mailLabelName_() {
  return PropertiesService.getScriptProperties().getProperty('LUMA_GMAIL_LABEL') || 'LumaQuote';
}

/** Return the lowercase address inside a From or Reply-To header, or '' when there is none. */
function mailAddress_(header) {
  var text = String(header || '');
  var angle = text.match(/<([^<>\s]+@[^<>\s]+)>/);
  var plain = text.match(/[^\s<>"',;]+@[^\s<>"',;]+/);
  return ((angle && angle[1]) || (plain && plain[0]) || '').toLowerCase();
}

/**
 * Self-test mode for a single-account test (Script Property LUMA_MAIL_SELF_TEST_TO, empty by default):
 * the account's own mail counts as a customer mail only when its To header contains that exact address
 * (for example the +quotes alias). The agent's replies go to the plain address, so they are still skipped.
 */
function isSelfTestMail_(message) {
  var target = (PropertiesService.getScriptProperties().getProperty('LUMA_MAIL_SELF_TEST_TO') || '').toLowerCase();
  return target !== '' && String(message.getTo() || '').toLowerCase().indexOf(target) >= 0;
}

/** Turn on self-test mode for this account's +quotes alias (run once in the editor; clear the property to stop). */
function enableMailSelfTest() {
  var parts = Session.getEffectiveUser().getEmail().toLowerCase().split('@');
  PropertiesService.getScriptProperties().setProperty('LUMA_MAIL_SELF_TEST_TO', parts[0] + '+quotes@' + parts[1]);
}

/** Turn self-test mode off again. */
function disableMailSelfTest() {
  PropertiesService.getScriptProperties().deleteProperty('LUMA_MAIL_SELF_TEST_TO');
}

/** Collect up to five labelled mails newer than the cursor, oldest first, skipping the account's own messages. */
function pendingMails_(cursor) {
  var me = Session.getEffectiveUser().getEmail().toLowerCase();
  var label = mailLabelName_().replace(/\s+/g, '-');
  var query = 'label:' + label + ' after:' + Math.floor(cursor / 1000 - 60);
  var items = [];
  GmailApp.search(query, 0, 50).forEach(function eachThread_(thread) {
    /** Consider every message of a labelled thread; later replies arrive in the same thread. */
    thread.getMessages().forEach(function eachMessage_(message) {
      /** Keep only customer messages newer than the cursor. */
      var at = message.getDate().getTime();
      var own = mailAddress_(message.getFrom()) === me;
      if (at > cursor && !message.isDraft() && (!own || isSelfTestMail_(message))) {
        items.push({ message: message, at: at });
      }
    });
  });
  items.sort(function byDate_(a, b) {
    /** Oldest first so the cursor never skips an earlier unsent mail. */
    return a.at - b.at;
  });
  return items.slice(0, MAIL_BATCH);
}

/** Convert one Gmail message into the fields the backend schema accepts (all untrusted content). */
function mailPayload_(item) {
  var message = item.message;
  return {
    message_id: message.getId(),
    thread_id: message.getThread().getId(),
    from_header: String(message.getFrom()).slice(0, 400),
    reply_to: String(message.getReplyTo() || '').slice(0, 400),
    subject: String(message.getSubject() || '').slice(0, 300),
    date_ms: item.at,
    auth_results: String(message.getHeader('Authentication-Results') || '').slice(0, 4000),
    body: String(message.getPlainBody() || '').slice(0, MAIL_BODY_CHARS),
    attachments: message.getAttachments({ includeInlineImages: false }).length
  };
}

/** Push the next batch of labelled mails; the cursor advances only after the backend stored them. */
function pollLumaMail() {
  var config = configuration_();
  var lock = LockService.getScriptLock();
  lock.waitLock(LOCK_WAIT_MS);
  try {
    var properties = PropertiesService.getScriptProperties();
    var cursor = Number(properties.getProperty('LUMA_MAIL_CURSOR') || String(Date.now() - MAIL_FIRST_RUN_MS));
    var items = pendingMails_(cursor);
    if (!items.length) return;
    var response = signedExportPost_(config, '/mail/inbound', { event: 'gmail_messages',
      messages: items.map(mailPayload_) });
    properties.setProperty('LUMA_LAST_MAIL_STATUS', String(response.status));
    if (response.status !== 200) throw new Error('Mail push was not accepted; check backend configuration and the connection.');
    properties.setProperty('LUMA_MAIL_CURSOR', String(items[items.length - 1].at));
  } finally {
    lock.releaseLock();
  }
}

/** Return the id of the newest message this account sent in a thread, or null when none is visible yet. */
function ownMessageId_(thread) {
  if (!thread) return null;
  var me = Session.getEffectiveUser().getEmail().toLowerCase();
  thread.refresh();
  var messages = thread.getMessages();
  for (var index = messages.length - 1; index >= 0; index--) {
    if (mailAddress_(messages[index].getFrom()) === me) return messages[index].getId();
  }
  return null;
}

/** Send one claimed reply and report it; replies in-thread only when the original reply address is the recipient. */
function sendOneMail_(config, mail) {
  var errorCode = null;
  var sentId = null;
  try {
    var options = {};
    if (mail.attachment) {
      var bytes = Utilities.base64Decode(mail.attachment.pdf_base64);
      if (sha256Hex_(bytes) !== mail.attachment.sha256 || bytes.length !== mail.attachment.size) {
        errorCode = 'transfer_corrupt';
      } else {
        options.attachments = [Utilities.newBlob(bytes, 'application/pdf', mail.attachment.filename)];
      }
    }
    if (!errorCode) {
      var original = mail.reply_message_id ? GmailApp.getMessageById(mail.reply_message_id) : null;
      var replyAddress = original ? mailAddress_(original.getReplyTo() || original.getFrom()) : '';
      if (original && replyAddress === mail.to) {
        original.reply(mail.body, options);
        sentId = ownMessageId_(original.getThread());
      } else {
        GmailApp.sendEmail(mail.to, mail.subject, mail.body, options);
        var sent = GmailApp.search('in:sent to:' + mail.to, 0, 1);
        sentId = sent.length ? ownMessageId_(sent[0]) : null;
      }
    }
  } catch (error) {
    errorCode = errorCode || 'send_error';
  }
  var receipt = signedExportPost_(config, '/mail/receipt', { event: 'gmail_send_receipt',
    dispatch_id: mail.dispatch_id, claim_token: mail.claim_token, outcome: errorCode ? 'failed' : 'sent',
    gmail_message_id: errorCode ? null : sentId, error_code: errorCode });
  PropertiesService.getScriptProperties().setProperty('LUMA_LAST_MAIL_SEND_STATUS', String(receipt.status));
}

/** Claim and send up to three queued replies per run under the script lock; the backend never resends a claimed one. */
function sendLumaMail() {
  var config = configuration_();
  var lock = LockService.getScriptLock();
  lock.waitLock(LOCK_WAIT_MS);
  try {
    for (var count = 0; count < 3; count++) {
      var claim = signedExportPost_(config, '/mail/claim', { event: 'gmail_send_claim' });
      if (claim.status !== 200) {
        PropertiesService.getScriptProperties().setProperty('LUMA_LAST_MAIL_SEND_STATUS', String(claim.status));
        throw new Error('Mail claim was not accepted; check backend configuration and the connection.');
      }
      if (!claim.body || !claim.body.mail) return;
      sendOneMail_(config, claim.body.mail);
    }
  } finally {
    lock.releaseLock();
  }
}

/** Check the label exists, then install one one-minute trigger each for polling and sending. */
function installLumaMail() {
  if (!GmailApp.getUserLabelByName(mailLabelName_())) {
    throw new Error('Create the Gmail label ' + mailLabelName_() + ' and a filter that applies it first.');
  }
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    ScriptApp.getProjectTriggers().forEach(function removeDuplicateMail_(trigger) {
      /** Replace only this integration's own mail triggers. */
      var handler = trigger.getHandlerFunction();
      if (handler === 'pollLumaMail' || handler === 'sendLumaMail') ScriptApp.deleteTrigger(trigger);
    });
    ScriptApp.newTrigger('pollLumaMail').timeBased().everyMinutes(1).create();
    ScriptApp.newTrigger('sendLumaMail').timeBased().everyMinutes(1).create();
  } finally {
    lock.releaseLock();
  }
}
