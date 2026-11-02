# Showcase shot list (90-120 seconds)

A truthful outline for a recorded walkthrough of the local app. Every shot is labeled **Real**
(runs in this repository today), **Local substitute** (the real code with a simulated channel or
stand-in) or **Not shown** (must not appear as working). Business impact is a pilot hypothesis;
the supplier and all records are fictional and synthetic. Do not state or imply revenue, time
saved, a client, live WhatsApp, a live Google Drive copy or human-speech accuracy.

Screenshots from the 2026-11-02 verified browser run are in
[`evidence/screenshots/2026-11-02/`](evidence/screenshots/2026-11-02). Before recording, run
`npm run setup`, start the stack as in [LOCAL_DEVELOPMENT.md](../LOCAL_DEVELOPMENT.md), and use
**Capture mode** in the app header so no private value appears on screen. Never show `.env`,
`.local/`, Supabase Studio or any token.

| # | Seconds | Show | Say (must stay true) | Label |
| --- | --- | --- | --- | --- |
| 1 | 0-8 | Inbox with one customer request and the "Synthetic supplier data" header | "A commercial-lighting supplier's sales workspace. All data is fictional." | Real |
| 2 | 8-22 | A customer text, then a voice note and a label photo in the thread; open the private preview | "Customers write, send voice notes and photos. Media is stored privately and treated as unconfirmed." Do not say it was transcribed unless you recorded a run with paid AI on. | Local substitute (upload is local-test; reading is off unless you enable paid AI) |
| 3 | 22-35 | The clarification the agent asks, then the customer's written reply | "A voice note or a photo can never confirm an order. Only a complete written SKU and quantity can." | Real (policy and tests); the agent runs offline unless paid AI is on |
| 4 | 35-55 | Quotation workspace: lines, catalog evidence page, subtotal, stock note | "Totals are exact decimal arithmetic from catalog prices. Stock is observed, not reserved." | Real |
| 5 | 55-70 | Edit a quantity to show the stale-edit conflict, then revision 2 | "A newer revision invalidates the old approval." | Real |
| 6 | 70-85 | Salesperson approves the exact revision; delivery shows "Delivered in local test" | "Approval binds to this exact revision and is rechecked before any send. Here the send is local." | Local substitute |
| 7 | 85-95 | Take over the conversation and write a human reply | "A salesperson can take over; queued automated replies stop." | Real |
| 8 | 95-105 | Portrait width of the same screen | "It works on a narrow screen." | Real |
| 9 | 105-120 | Closing card with what is not done | "WhatsApp and Google Drive are implemented and tested against stand-ins; live accounts are not connected yet." | Real statement |

## Not shown (do not demonstrate or claim)

- A real WhatsApp message, receipt or phone (adapter exists, mock-tested only; needs the steps in
  [MORNING_ACTIONS.md](MORNING_ACTIONS.md)).
- A file appearing in Google Drive or a live Sheet import beyond what the Google evidence records.
- Voice or photo accuracy numbers: the development run used synthetic speech and drawn labels, the
  holdout has not been run, and the model had known flakes.
- The interactive 3D scene's performance (not measured here); use the static view if the capture is
  not smooth, and honor reduced motion.

## Reproducible evidence behind each claim

- Workflow and approval: `npm run test:browser`, [workflows](WORKFLOWS.md), `tests/integration`.
- Written-confirmation rule: [TESTING_PLAN.md](TESTING_PLAN.md) section 9, `tests/unit/test_requirement_policy.py`.
- Agent evaluation and its limits: [evaluation README](../tests/fixtures/evaluation/README.md) and the dated
  [evidence](evidence/evaluation-development-agent-2026-11-02.json).
- Gate results: [checkpoint evidence](evidence/checkpoint-2026-11-02.json).
