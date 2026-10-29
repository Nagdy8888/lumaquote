from luma.features.conversations.repository import conversation
from luma.features.quotations.repository import latest_quote


def workspace(conn, member):
    """Read company-scoped workspace collections and actual stored aggregates for the authorized staff view."""
    company = member["company_id"]
    company_row = conn.execute("select * from luma.companies where id=%s", (company,)).fetchone()
    conversations = conn.execute(
        """select c.*, (select body from luma.messages m where m.conversation_id=c.id
        order by m.created_at desc limit 1) preview from luma.conversations c where company_id=%s
        order by updated_at desc limit 100""",
        (company,),
    ).fetchall()
    quotes = conn.execute(
        """select q.*,c.customer_name,c.customer_company,
        (select status from luma.outbox o where o.quote_id=q.id limit 1) delivery
        from luma.quotes q join luma.conversations c on c.id=q.conversation_id
        where q.company_id=%s order by q.created_at desc limit 100""",
        (company,),
    ).fetchall()
    return {
        "company": company_row,
        "role": member["role"],
        "conversations": conversations,
        "quotes": quotes,
        "products": conn.execute(
            "select * from luma.products where company_id=%s order by family,sku", (company,)
        ).fetchall(),
        "sources": conn.execute(
            "select * from luma.sources where company_id=%s order by title", (company,)
        ).fetchall(),
        "activity": conn.execute(
            "select * from luma.audit where company_id=%s order by id desc limit 20", (company,)
        ).fetchall(),
        "jobs": conn.execute(
            "select id,conversation_id,kind,status,error_code from luma.jobs where company_id=%s order by created_at desc limit 20",
            (company,),
        ).fetchall(),
        "usage": conn.execute(
            """select coalesce(sum(case when status in ('reserved','unknown') then reserved
                when status='settled' then estimated else 0 end),0) estimated_or_reserved from luma.usage where company_id=%s""",
            (company,),
        ).fetchone(),
    }


def detail(conn, company, cid):
    """Return scoped conversation, ordered messages, latest quotation, and delivery records for the working inbox."""
    return {
        "conversation": conversation(conn, company, cid),
        "messages": conn.execute(
            "select m.*, (m.actor='staff' and m.provider_id is not null) as outbound, a.status as media_status, (a.normalized_path is not null) as audio_available from luma.messages m left join luma.media a on a.message_id=m.id and a.company_id=m.company_id where m.company_id=%s and m.conversation_id=%s order by m.created_at,m.id",
            (company, cid),
        ).fetchall(),
        "quote": latest_quote(conn, company, cid),
        "delivery": conn.execute(
            "select id,kind,status,error_code,updated_at,case when kind='reply' then payload->>'text' end as preview from luma.outbox where company_id=%s and conversation_id=%s order by created_at desc",
            (company, cid),
        ).fetchall(),
    }
