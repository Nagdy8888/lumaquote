# Runbook: <alert or symptom>

- **Alert:** `<alert-name>` (link to alert definition in your monitoring tool)
- **Severity:** sev2 (sev1 if <stronger condition>)
- **Impact:** <one sentence — who/what is affected>
- **Owner team:** <team name>
- **Last verified:** YYYY-MM-DD by @name

## Dashboards & queries

- [<dashboard 1>](<url>) — link, not just name
- [<dashboard 2>](<url>)
- [Recent errors (Sentry)](<url>)
- [Logs (Datadog / Cloudwatch)](<url>)

## Diagnose

1. Open the [<dashboard 1>](<url>). Is it global or scoped to a single route / region?
2. Open the [errors view](<url>). What's the top error class in the last 15 min?
3. Check recent deploys: `gh run list -w deploy-<service> -L 5`. Did errors start within 5 min of a deploy?
4. Check downstream dependencies: <service status pages, IdP, payment provider>.

## Remediate

**If correlated with a recent deploy** (most common):
1. Roll back: `gh workflow run rollback-<service>.yml -f sha=<previous-sha>`.
2. Watch the [<dashboard 1>](<url>) for 5 minutes.

**If a single route / endpoint is the source:**
1. Open the [errors view](<url>) filtered to that route.
2. If it's a downstream timeout, follow the matching runbook: `runbooks/<downstream>-slow.md`.
3. If it's a code bug, file a sev2 ticket and decide: rollback vs hotfix vs revert that route.

**Last resort: scale out.**
1. `kubectl scale deploy/<service> --replicas=<2x current>`. Disruptive: brief connection churn.

## Verify

- <Concrete metric> < <threshold> for <duration> consecutive on [<dashboard 1>](<url>).
- No new errors for the affected route in the last 5 min on the [errors view](<url>).
- <Service status page> green.

## Comms

- **Sev2:** post in `#incidents` on detection, every 30 min, on resolution.
- **Sev1:** add a status page incident + post in `#incidents` every 15 min.

## Escalate

1. **<Team> on-call** — first try. (PagerDuty: link)
2. **<Lead>** — if on-call doesn't respond within 10 min. (PagerDuty: link)
3. **<Higher>** — for sev1 lasting > 30 min. (PagerDuty: link)

## Postmortem trigger

This incident produces a postmortem when:

- Sev1, any duration.
- Sev2 lasting > 30 min.
- Any incident with data loss, even if otherwise sev3.

See [postmortems/](../postmortems/) for the template and process.
