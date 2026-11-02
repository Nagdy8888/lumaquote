# Feature boundaries

Follow existing paths first. A possible small starting layout has application bootstrap/router/providers, feature modules for conversations and quotations, and shared UI/API utilities. Add domain entities or composite widgets only when reuse or complexity warrants them.

Give each feature a small public interface. External imports should not reach into its private mutation or component implementation. Avoid a single giant shared barrel that loads the entire UI or creates circular imports.
Within a feature, add ui, model, api, or helpers only when needed. Do not scatter one behavior across many shallow files just to satisfy a folder diagram.
Keep API endpoint definitions, query keys, response schemas, and error interpretation near the behavior that uses them. Share only when at least two real consumers need the same contract.

Hooks need correct dependencies and cleanup. Name complex callbacks when doing so clarifies traces; a blanket requirement for named function expressions is not a substitute for correct closure behavior.
Keep effects for external synchronization, not derived display data. Avoid duplicate state representations that drift from the server or query cache.
Ensure routing, asynchronous state, and lazy-loaded 3D have error/fallback boundaries. An optional visual enhancement must not block access to quotation or approval tasks.
Tests should exercise behavior through feature/public interfaces. Verify import boundaries where they prevent actual cycles or framework leakage, not by counting folders or comment banners.

