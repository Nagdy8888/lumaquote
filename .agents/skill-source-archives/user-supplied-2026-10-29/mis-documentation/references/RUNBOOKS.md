# Runbooks

A **runbook** is the doc that fires when an alert pages someone or a known issue recurs. Optimised for the 3am-tired-oncall reader.

Runbooks differ from how-to guides in three ways:

| Aspect             | How-to guide         | Runbook                                  |
|--------------------|----------------------|------------------------------------------|
| Trigger            | Reader chooses it    | An alert / symptom forces them to it     |
| Time pressure      | Low                  | High (incident in progress)               |
| Severity required  | No                   | Yes (sev1 / sev2 / sev3)                 |
| Escalation path    | Optional             | Required                                 |

If a doc is "things you might want to do someday", it's a how-to. If a doc is "things you must do right now to stop the bleeding", it's a runbook.

## File layout

```
docs/runbooks/
├── README.md                        # index
├── api-error-rate-high.md            # alert name → runbook
├── checkout-500s.md
├── database-cpu-saturated.md
├── stripe-webhook-backlog.md
└── ...
```

- **Filename = alert name (kebab-case)**, so the on-caller can match the page to the doc instantly.
- One runbook per alert / symptom. Combining unrelated alerts into one runbook costs time at 3am.

## Required sections

Template: `assets/template-runbook.md`. Sections, in order:

1. **Alert / symptom** — what triggers this runbook
2. **Severity** — sev1 / sev2 / sev3 with our definitions
3. **Impact** — who/what is affected
4. **Owner team** — who owns the underlying system
5. **Dashboards & queries** — links, not names
6. **Diagnose** — fast checks, in priority order
7. **Remediate** — exact commands, in order
8. **Verify** — how you know it's fixed
9. **Comms** — who to update and when
10. **Escalate** — who to page if the above fails
11. **Postmortem trigger** — when this incident produces a postmortem

## Severity ladder

| Sev   | Definition                                                                  |
|-------|-----------------------------------------------------------------------------|
| sev1  | User-facing outage or data loss. Wake people up.                              |
| sev2  | Significant degradation, partial outage, or imminent sev1. Within an hour.   |
| sev3  | Low-impact issue worth tracking but not paging on overnight.                  |

Every runbook states its severity. If an alert has multiple severity tiers, link to separate runbooks per tier.

## Writing rules

- **3am-readable.** Numbered steps, no narrative paragraphs.
- **Every command is copy-pasteable.** No "edit X then run Y" — write both as separate steps.
- **Every link is live.** "Check the API latency dashboard" → linked. Same for queries (Grafana / Datadog URLs preserve filters).
- **Diagnose before remediate.** A runbook that jumps to restart-the-service before confirming the symptom causes outages.
- **Each remediation step has a confidence note.** "Safe: read-only" / "Disruptive: kicks active sessions" / "Last resort: drops in-flight orders".
- **Verify is a real step, not a vibe.** "API error rate < 0.5% for 5 consecutive minutes on $dashboard$" beats "things look better".

## Example skeleton (truncated)

```markdown
# Runbook: API error rate high

- **Alert:** `api-5xx-rate > 1% for 5min`
- **Severity:** sev2 (sev1 if > 5% or sustained > 30min)
- **Impact:** Customer-facing 5xx on the API. Mobile + web both affected.
- **Owner team:** Platform API
- **Dashboards:**
  - [API error rate (Grafana)](https://grafana.internal/d/api-errors)
  - [Top error sources (Sentry)](https://sentry.io/...)

## Diagnose
1. Open the [API error rate dashboard](...). Is it global or a single
   route / region?
2. Open [Sentry](...). What's the top error class in the last 15 min?
3. Check the latest deploy: `gh run list -w deploy-api -L 5`. Did errors
   start within 5 minutes of a deploy?

## Remediate
**If correlated with a recent deploy** (most common):
1. Roll back: `gh workflow run rollback-api.yml -f sha=<previous-sha>`.
2. Watch the dashboard for 5 minutes.

**If a single route**:
1. Open Sentry's view for that route. Check the stack trace.
2. If it's a downstream timeout, see `runbooks/<downstream>-slow.md`.

**Last resort: scale out**:
1. `kubectl scale deploy/api --replicas=20` (was 10). Disruptive: kicks
   metrics for 30s.

## Verify
- API error rate < 0.5% for 5 consecutive minutes on the [error dashboard](...).
- Sentry shows no new errors for the affected route in the last 5 min.

## Comms
- **Sev2:** post in `#incidents` on detection, every 30 min, on resolution.
- **Sev1:** add a status page incident + post in `#incidents` every 15 min.

## Escalate
1. **Platform API on-call** — try them first (the runbook author's team).
2. **Platform Lead** — if on-call doesn't respond within 10 min.
3. **CTO** — for sev1 lasting > 30 min.

## Postmortem trigger
This runbook produces a postmortem when:
- Sev1 of any duration.
- Sev2 lasting > 30 min.
- Any incident with data loss, even if otherwise sev3.
```

## Maintenance

- **The runbook's author is on the hook for keeping it accurate.** When the underlying system changes, the author updates the runbook in the same PR.
- **Mark the `last verified` date** in the runbook. Re-verify quarterly during a low-traffic window — pretend an alert just fired and walk through the runbook.
- **After every real incident, update the runbook.** Whatever the on-caller wished they'd known goes in.

## Discovery

Runbooks live under `docs/runbooks/`. The alert in the monitoring system links directly to the runbook URL (PagerDuty / Grafana / Datadog all support this). That link is part of the alert definition — runbooks that aren't linked from alerts are dead.

## Anti-patterns

- Narrative prose runbooks. "Check the latency, and if it's high, you might want to consider scaling out." → "1. Open $dashboard$. 2. If P99 > 500ms, run `kubectl scale ...`."
- Runbooks with no `Verify` section. The on-caller doesn't know they're done.
- Runbooks that escalate to "Slack #platform". That's not an escalation path — name the on-call.
- A runbook covering five unrelated alerts because they hit the same service. Split them.
- Runbooks living in a separate wiki (Confluence, Notion) that the alert can't deep-link. Co-locate with code.
- "TODO: investigate" left in remediation steps. Investigate now or remove the step.
