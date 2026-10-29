# Architecture — Containers (C4 Level 2)

Zoom into `<Product name>` from the [System Context](./context.md). Each box below is an independently-runnable unit (a service, app, datastore, or message broker). The C4 use of "container" predates Docker — it doesn't mean Docker container specifically.

```mermaid
C4Container
    title Containers — <Product name>

    Person(customer, "Customer")
    Person(admin,    "Admin")

    System_Boundary(product, "<Product name>") {
        Container(web,        "Web app",        "Next.js / React",       "Customer-facing UI.")
        Container(admin_web,  "Admin web",      "Next.js / React",       "Internal admin UI.")
        Container(api,        "API",            "Python / FastAPI",      "REST API for web + mobile.")
        Container(worker,     "Worker",         "Python / Celery",       "Async jobs (email, fulfilment).")
        ContainerDb(db,       "Primary DB",     "Postgres 16",           "Orders, users, catalogue.")
        ContainerDb(cache,    "Cache",          "Redis 7",               "Sessions, rate-limit counters.")
        ContainerQueue(bus,   "Event bus",      "Redis Streams",         "Cross-service events.")
    }

    System_Ext(stripe,   "Stripe")
    System_Ext(postmark, "Postmark")

    Rel(customer,  web,       "Uses",                          "HTTPS")
    Rel(admin,     admin_web, "Uses",                          "HTTPS")
    Rel(web,       api,       "Calls",                         "HTTPS / JSON")
    Rel(admin_web, api,       "Calls",                         "HTTPS / JSON")

    Rel(api,    db,    "Reads / writes",        "SQL / TCP")
    Rel(api,    cache, "Reads / writes",        "RESP / TCP")
    Rel(api,    bus,   "Publishes order events","RESP / Streams")
    Rel(worker, bus,   "Consumes order events", "RESP / Streams")
    Rel(worker, db,    "Reads / writes",        "SQL / TCP")

    Rel(api,    stripe,   "Charges cards",                "HTTPS / Stripe API")
    Rel(worker, postmark, "Sends order email",            "HTTPS / Postmark API")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Containers

- **Web app (Next.js)** — customer-facing UI. Server-rendered pages + client islands. Talks only to the API.
- **Admin web (Next.js)** — separate UI for internal admins. Auth gated.
- **API (FastAPI)** — REST API consumed by the web + mobile clients. Owns business logic.
- **Worker (Celery)** — async job runner. Drains the event bus and the delayed-job queue.
- **Primary DB (Postgres 16)** — source of truth for orders, users, catalogue.
- **Cache (Redis 7)** — session store, rate-limit counters, hot lookups.
- **Event bus (Redis Streams)** — cross-service event transport ([ADR-0002](../../decisions/0002-event-bus-on-redis-streams.md)).

## Notable flows

- **Customer order:** Web → API → DB (write order, status=pending) → Bus (`order.created`) → Worker → Stripe (charge) → DB (status=paid) → Bus (`order.paid`) → Worker → Postmark (confirmation email).
- **Admin update:** Admin Web → API → DB.

## What's next

- [Components (C4 L3)](./components/) — zoom into a specific container.
- [Decisions](../../decisions/README.md) — why we chose Postgres, Redis Streams, etc.

## Maintenance

- **Last verified:** YYYY-MM-DD by @name.
- **When to update:** any time a container is added, removed, or its protocol / responsibility changes materially.
