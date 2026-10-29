# Verified OpenAI contracts

Checked against official documentation on October 29, 2026, and the installed
Python SDK declarations before the synthetic live canaries.

- [File transcription](https://developers.openai.com/api/docs/guides/speech-to-text)
  documents `gpt-transcribe`, completed-file uploads and the plural `languages`
  hint. The app submits sandbox-normalized WAV with `languages=["en"]` and checks
  detected languages; it does not translate unknown-language speech into an offer.
- [Python transcription reference](https://developers.openai.com/api/reference/python/resources/audio/subresources/transcriptions/methods/create)
  defines the file upload, JSON response and detected-language fields. The current
  SDK exposes these fields directly; no undocumented replacement method is used.
- [GPT-Transcribe model](https://developers.openai.com/api/docs/models/gpt-transcribe)
  lists $0.0045/minute. Duration-derived amounts remain estimates; provider billing
  has not been retrieved.
- [GPT-6 Luna model](https://developers.openai.com/api/docs/models/gpt-6-luna)
  documents Responses and `reasoning.effort=none`. Extraction requests explicitly
  select Standard processing (`service_tier="default"`), bound input/output, and
  disable response storage. The configured model must match the verified policy.
- [Pricing](https://developers.openai.com/api/docs/pricing)
  lists Standard short-context Luna input/output rates of $0.10/$0.50 per million
  tokens. Current token estimates do not claim invoice parity or include a
  separately verified billing retrieval path.

Provider credentials and recorded speech remain backend-only. Automatic raw
LangGraph/model tracing is disabled. LangSmith receives only an opaque job UUID
and allowlisted outcome through a separate optional export; its account quota
currently blocks live export. See [progress evidence](evidence/phase-3-progress.json)
and [morning actions](MORNING_ACTIONS.md).
