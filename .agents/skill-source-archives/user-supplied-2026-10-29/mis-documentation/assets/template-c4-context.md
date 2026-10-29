# Architecture — System Context (C4 Level 1)

<One paragraph: what the system does at the highest level. The reader of this
diagram is anyone in the company — not necessarily an engineer.>

```mermaid
C4Context
    title System Context — <Product name>

    Person(customer,     "Customer",      "Places and tracks orders.")
    Person(admin,        "Admin",         "Manages the catalogue and users.")
    Person(oncall,       "Oncall Engineer","Responds to alerts.")

    System(product, "<Product name>", "Accepts orders, processes payments, fulfils them.")

    System_Ext(stripe,    "Stripe",         "Payment processing")
    System_Ext(postmark,  "Postmark",       "Transactional email")
    System_Ext(sentry,    "Sentry",         "Error tracking")
    System_Ext(idp,       "Customer IdP",   "SSO / OIDC")

    Rel(customer, product, "Places orders, views status", "HTTPS / web + mobile")
    Rel(admin,    product, "Manages catalogue & users",    "HTTPS / admin web")
    Rel(oncall,   product, "Operates",                     "HTTPS / dashboards")

    Rel(product, stripe,   "Charges cards",                "HTTPS / Stripe API")
    Rel(product, postmark, "Sends order confirmations",    "HTTPS / Postmark API")
    Rel(product, sentry,   "Reports errors",               "HTTPS")
    Rel(product, idp,      "Federates auth",               "OIDC")

    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Persons

- **Customer** — end users who place orders.
- **Admin** — internal staff managing the catalogue and accounts.
- **Oncall Engineer** — operations role; reads dashboards, responds to alerts.

## External systems

- **Stripe** — handles all card processing. We never store PANs.
- **Postmark** — delivery of transactional email (order confirmations, password resets).
- **Sentry** — error tracking from the API, web, and mobile clients.
- **Customer IdP** — SSO for enterprise customers via OIDC.

## What's next

- [Containers (C4 L2)](./containers.md) — zoom in on what's inside `<Product name>`.

## Maintenance

- **Last verified:** YYYY-MM-DD by @name.
- **When to update:** any time a new external system is added or removed, or a new persona is introduced.
