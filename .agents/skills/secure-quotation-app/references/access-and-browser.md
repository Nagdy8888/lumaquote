# Access, sessions, and browser boundaries

## Definitions
Authentication establishes identity; authorization decides an action on a resource. RBAC assigns role permissions; RLS filters database rows. IDOR/BOLA is access to another principal's object by changing an identifier. CSRF abuses browser-attached credentials; XSS executes hostile content in the application's origin. CORS is a browser sharing policy, not authentication.

## Supabase and staff access
Verify tokens using the deployed Supabase signing configuration, including allowed algorithm, signature, issuer, audience, and time claims. Use bounded JWKS caching and rotation handling where asymmetric keys apply. Local signing behavior must not silently weaken production verification.
Resolve current membership and role for approvals, exports, administration, and access to private data. A signed token can outlive a membership change. Staff, customer-channel, worker, and administration identities have different authority.
Define the actual role/action matrix in the spec. Do not treat knowing a phone number, thread ID, quote ID, or company ID as authorization. A verified WhatsApp sender is still not an authenticated salesperson.
Use Supabase Auth's supported recovery/session controls. Verify current sign-out and token-revocation semantics; do not claim already issued JWTs become instantly invalid without an enforcing membership/session check.
For privileged account actions, use reauthentication/MFA appropriate to the chosen deployment and threat model. Prevent role/membership changes through self-editable user metadata.

Use schema-qualified migrations with explicit grants and RLS for exposed business tables. INSERT/UPDATE checks must prevent company or owner reassignment; cover SELECT/INSERT/UPDATE/DELETE, views, and RPC functions.
Separate restricted quote/approval transitions from ordinary editable fields so direct REST writes cannot approve or send a quote. RLS is not automatically enforced for table owners, superusers, bypassrls roles, or elevated functions. A PostgreSQL connection using postgres does not prove tenant isolation.
Use narrowly privileged worker identities and check object scope in their services. Security-definer functions need a justified use, fixed safe search_path, schema-qualified objects, and restricted execute grants. Prefer invoker privileges where appropriate.
Keep files in private buckets. Derive object paths server-side; authorize upload/read/delete/sign operations. Validate a scoped upload again before accepting it into ingestion. Short-lived signed URLs remain bearer capabilities until expiry; redaction and narrow expiry are necessary, and immediate revocation needs an explicit design.

## Browser and API
Choose the session transport deliberately. For cookie-attached credentials, use suitable HttpOnly/Secure/SameSite attributes and server-side CSRF protection for mutations. For bearer-token requests, avoid accidental cookie fallback; XSS can still steal accessible tokens.
Configure exact development/production origins and trusted reverse proxies. Wildcard CORS or forwarded headers cannot grant access. Use HTTPS for an externally deployed app; local HTTP is confined to local development.
React escapes ordinary text, but sanitize any deliberately enabled rich HTML/Markdown and restrict link protocols. Render customer/catalog text, filenames, and model output as hostile input. A content security policy is defense in depth, not a replacement for safe rendering.
Apply suitable content-type, clickjacking/frame, referrer, and cache controls. Private quotations, audio, and responses must not enter public caches. Audit frontend build output for provider keys, database URLs, service-role secrets, and internal trace links.
Bound filters/pagination and use parameterized database queries. Validation schemas must reject unrecognized privilege-bearing fields and invalid business values; frontend validation alone is insufficient.

## References
- [Supabase RLS](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase Auth rate limits](https://supabase.com/docs/guides/auth/rate-limits)
- [OWASP REST security](https://cheatsheetseries.owasp.org/cheatsheets/REST_Security_Cheat_Sheet.html)
- [OWASP CSRF prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html)

