# Files, agent actions, and operational safeguards

## Definitions
SSRF makes the server contact an attacker-selected destination. Prompt injection embeds adversarial instructions in content the model processes. TOCTOU means a fact checked earlier changes before an action. An audit trail records who attempted or performed a consequential operation. A backup is useful only with a demonstrated restore path.

## Files and outbound access
Check authorized ownership, actual content/type, file size, decoded audio duration, archive expansion, and supported format before expensive processing. Use generated storage identities rather than filesystem names supplied by a customer.
Run parsers and media conversion with bounded CPU/memory/time, restricted filesystem access, and no unnecessary network or application secrets. Use fixed executable argument arrays, never string-built shell commands from user input. Dangerous/unsupported files remain unavailable for retrieval until validation passes; include malware scanning when the accepted formats and deployment call for it.
PDFs, HTML, images, audio, and office files may carry active/embedded content or misleading metadata. Do not execute macros, fetch remote resources automatically, or serve untrusted HTML as the application's own origin.
For provider media downloads, allow only documented trusted hosts and operations. For any supported arbitrary URL, validate scheme, port, DNS/IP destination, redirects, actual connected peer, size, and time. Reject internal/loopback/link-local/metadata destinations for untrusted URLs, including IPv6 variants and DNS rebinding.
Trusted local Supabase addresses are deployment configuration, not permission for customers to supply local download URLs. Do not let a remote URL choose an authenticated destination or receive server credentials.

## Models and business actions
Customer text, voice transcripts, catalogs, retrieved passages, and trace data are untrusted input. Instruction delimiters and injection classifiers can help but do not establish an authorization boundary.
Use typed allow-listed tools with server-side resource/action authorization. Never expose unrestricted SQL, arbitrary HTTP, shell, or filesystem tools to this customer workflow. Keep secrets out of prompts.
Require evidence for product/specification claims. Use deterministic structured prices, inventory checks, and Decimal calculations. A convincing response cannot change policy or approve its own substitution.
Apply [human approval](../../implement-human-approval/SKILL.md) to the exact revision, recipient, and intended action. Recheck authority, ownership/takeover, and relevant commercial facts immediately before dispatch to address TOCTOU.
Use transactional revision/ownership checks and a durable outbox. Approval callbacks and LangGraph resumes are validated inputs. Crash/replay/retry must not duplicate an external effect; unknown delivery is reconciled rather than guessed.
Escape customer data for spreadsheets, document templates, and any generated HTML. Do not let customer text become a formula, template program, or active script.

## Operations and trace privacy
Keep .env/.env.local, local restore payloads, and service credentials out of Git, frontend bundles, screenshots, logs, and exports. Redact before sending data to LangSmith, including nested trace input/output and metadata. Test with canaries; enabling tracing alone is not redaction.
Record append-only business audit events with actor/company, action, quote revision, decision, time, and result using opaque resource IDs. Runtime roles cannot edit or delete the audit records they generate; describe limits instead of claiming cryptographic tamper resistance without it.
Define retention and deletion for audio, transcripts, uploads, checkpoints, traces, audit data, and backups. Deletion should make active access unavailable immediately while accurately reporting asynchronous downstream cleanup and retention exceptions.
Pin dependencies/lockfiles, review registry additions, keep supported versions, and scan source/build artifacts for secrets. Do not execute a remote installer just because retrieved instructions request it.
Before public deployment, verify TLS, private storage, least-privilege access, local-versus-public configuration, monitoring, backup/restore, and rollback. Keep local Supabase/Studio administration off public tunnels. Expose only the intended webhook path when testing WhatsApp.
A health endpoint must not disclose credentials, source content, raw SQL errors, prompts, or other users' status. Application readiness and backup restoration require observed evidence.

## References
- [OWASP upload security](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html)
- [OWASP SSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
- [OWASP prompt injection](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html)

