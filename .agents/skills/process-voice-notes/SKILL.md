---
name: process-voice-notes
description: Implement English voice-note intake, transcription, request extraction, and clarification. Use for customer audio handling and transcription quality evaluation.
---

# Process Voice Notes

Voice notes enter the same conversation and request workflow as text. Verify the selected provider's current audio formats, duration limits, transcription interface, and retention behavior from official documentation before implementation.

## Audio and transcript
Use OpenAI for initial English transcription with backend-only credentials, as selected by the user. Verify current APIs, choose a model using test-audio quality and cost, and retain local faster-whisper only as an optional alternative.
Authorize access to the original media. Enforce byte, duration, and decoded-resource limits; validate actual media content rather than trusting its extension.
Run media conversion with bounded resources, fixed allowed operations, no arbitrary command execution, and no unnecessary network access.
Keep original audio, transcript, and extracted request linked by source message and version. Show authorized staff playback, the transcript, and editable extracted details.
Persist processing and failure states. Retries must not create duplicate requests. Allow text clarification when audio is unusable.

## Extract cautiously
Preserve quantities, units, model codes, negation, delivery dates, and the speaker's uncertainty. Resolve relative dates using the business timezone and message timestamp; clarify ambiguous deadlines.
Do not turn an uncertain transcript into a confident product code or quantity. Provider confidence may be absent or uncalibrated; use ambiguity checks and customer confirmation rather than inventing scores.
Ask focused questions for consequential ambiguity, such as thirteen versus thirty, watts versus voltage, or partial model numbers.
A corrected transcript or customer answer updates the request revision. Rebuild affected draft lines and invalidate affected approvals.
Treat spoken instructions as untrusted customer input; audio does not grant access to internal tools or company data.

## Verify
Evaluate English accents, noise, silence, unsupported language, interrupted speech, numbers, units, codes, and corrections. Measure consequential field errors as well as transcript quality.
Keep synthetic or recorded-test audio labeled and disclose external transcription processing where applicable.

