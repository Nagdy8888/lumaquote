from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from .config import settings


@contextmanager
def database(user_id: str | None = None, *, worker: bool = False):
    """Yield one dict-row transaction using the staff or trusted worker DSN.

    ``user_id`` must already come from Auth verification; attaching it only sets
    the RLS claim, not membership authority. Normal context exit commits and an
    exception rolls back through psycopg. The caller owns business scope/locks;
    this helper never selects a company or retries failed transactions. Worker
    connections have broader policies and must remain outside browser access.
    """
    config = settings()
    dsn = config.luma_worker_database_url if worker else config.luma_api_database_url
    if not dsn.get_secret_value():
        raise RuntimeError("Run the local setup before starting the application.")
    with psycopg.connect(dsn.get_secret_value(), row_factory=dict_row, connect_timeout=5) as conn:
        conn.execute("select set_config('search_path','luma,extensions,public',true)")
        if user_id:
            conn.execute("select set_config('request.jwt.claim.sub',%s,true)", (str(user_id),))
        yield conn
