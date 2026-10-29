from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row

from .config import settings


@contextmanager
def database(user_id: str | None = None, *, worker: bool = False):
    """Yield a transactional restricted-role connection; attach the verified staff identity for RLS when provided."""
    config = settings()
    dsn = config.luma_worker_database_url if worker else config.luma_api_database_url
    if not dsn.get_secret_value():
        raise RuntimeError("Run the local setup before starting the application.")
    with psycopg.connect(dsn.get_secret_value(), row_factory=dict_row, connect_timeout=5) as conn:
        conn.execute("select set_config('search_path','luma,extensions,public',true)")
        if user_id:
            conn.execute("select set_config('request.jwt.claim.sub',%s,true)", (str(user_id),))
        yield conn
