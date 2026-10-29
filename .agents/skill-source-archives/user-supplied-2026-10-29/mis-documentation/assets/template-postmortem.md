# Postmortem: <short title> (YYYY-MM-DD)

- **Status:** draft | reviewed | published
- **Severity:** sev1 | sev2
- **Incident commander:** @name
- **Authors:** @name, @name
- **Date of incident:** YYYY-MM-DD
- **Published:** YYYY-MM-DD

## Summary

<3 sentences. What happened? What was the impact? How was it fixed?>

## Impact

- **Duration:** <start UTC> → <end UTC> (<duration>).
- **Users affected:** <approx count or %>.
- **Revenue / SLA impact:** <best estimate>.
- **Data loss?** <yes / no — if yes, scope>.
- **External comms:** <status page entries, customer emails sent>.

## Timeline (UTC)

| Time (UTC) | Event |
|------------|-------|
| HH:MM      | <Event — e.g. deploy of `<service>@<sha>` reaches production.> |
| HH:MM      | <Alert fires.> |
| HH:MM      | <On-call acks, opens incident channel `#incident-…`.> |
| HH:MM      | <Diagnose: cause identified.> |
| HH:MM      | <Mitigation begins.> |
| HH:MM      | <Mitigation complete — error rate / latency / etc. back to baseline.> |
| HH:MM      | <Status page updated to resolved.> |

## Root cause(s)

<Use 5-whys for a single chain, or a fault tree if multiple causes combined.>

**5-whys:**

```
<Symptom in plain language.>
  Why? <…>
    Why? <…>
      Why? <…>
        Why? <…>
          Why? <root cause>
```

**Or fault tree:**

```
                       <Outage in plain language>
                                  │
                ┌─────────────────┼─────────────────┐
                ▼                 ▼                 ▼
        <Cause A>           <Cause B>          <Cause C>
            │                   │                  │
            ▼                   ▼                  ▼
         <…>                  <…>                <…>
```

## Contributing factors

<Things that made it worse but weren't the cause. Slow alert routing, stale
runbook, oncall handover gap, etc.>

-
-

## Detection

- **How we found out:** <alert / customer report / employee / dashboard browse>.
- **Time to detect:** <minutes from impact start to first ack>.
- **Could we have detected sooner?** <yes / no — and how>.

## What went well

-
-

## What went poorly

<System gaps, not personal failures. Replace "X did Y" with "the process / tool / alert allowed Y".>

-
-

## Action items

1. **[P0]** <Action — concrete, shippable>.
   Owner: @name (Team). Due: YYYY-MM-DD. [TICKET-NNN](<tracker link>).
2. **[P1]** <Action>.
   Owner: @name (Team). Due: YYYY-MM-DD. [TICKET-NNN](<tracker link>).
3. **[P2]** <Action>.
   Owner: @name (Team). Due: YYYY-MM-DD. [TICKET-NNN](<tracker link>).

## Lessons learned

<Concrete things we now know. Not "be more careful" — what specifically would
we do differently?>

-
-

## Links

- Incident channel: `#incident-YYYY-MM-DD-<topic>`
- Related runbook(s): [runbooks/<alert>.md](../runbooks/<alert>.md)
- Related ADR(s): <links>
- Related RFC(s): <links>
- Status page: <link to incident>
