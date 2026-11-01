# Verified OpenAI contracts

Checked against official documentation on October 29, 2026, and the installed
Python SDK declarations before the synthetic live canaries.

For the surrounding implementation contracts, read [media processing](reference/MEDIA.md),
[catalog/index/query lifecycle](reference/CATALOG.md),
[agent allowance and tracing](reference/AGENT_RUNTIME.md) and
[configuration](reference/CONFIGURATION.md). This provider reference records
checked assumptions; it does not replace deterministic authorization or evaluation.

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

## Photo label-reading contract

The [official vision guide](https://developers.openai.com/api/docs/guides/images-vision?api-mode=responses)
documents Responses image inputs, including Base64 data URLs. The photo adapter
submits only sandbox-normalized JPEG bytes, with fixed `gpt-6-luna`, Standard
processing, bounded output and response storage disabled. Structured output
contains literal visible text, visible SKU identifiers and uncertainty. It does
not authorize requested quantities, price, compatibility, discounts or approval.

A synthetic-label canary passed with an estimated USD 0.000131 usage amount;
actual billing was not retrieved. The input was generated test data, not a client
photo or an accuracy evaluation. See [photo progress](evidence/photo-progress.json).
The embedding adapter is implemented and tested with deterministic provider
responses and a real synthetic index/query plumbing canary.

## Embedding adapter under development

The [official embedding guide](https://developers.openai.com/api/docs/guides/embeddings)
and [model reference](https://developers.openai.com/api/docs/models/text-embedding-3-small)
were checked against the installed SDK. The adapter fixes `text-embedding-3-small`,
1536 dimensions, float output, no automatic retries and disabled raw tracing.
It caps a batch at 500 nonempty records, 8000 UTF-8 bytes per record and 100000
bytes overall; the recorded rate is USD 0.02 per million input tokens. Returned
indices/dimensions/finite values must match before publication. Adapter code is
present and actual database publication/recovery tests pass with fake vectors.
A real three-record synthetic index/query canary passed with estimated usage
USD 0.0000024 combined; actual billing was not retrieved. The query embeds unchanged
evidence text, so this verifies plumbing rather than natural-language recall.
Semantic quality and the live graph fallback branch remain unverified.
