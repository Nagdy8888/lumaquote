"""Measure the current lexical lookup baseline on generated development queries, never the frozen holdout."""

import argparse
import json
import math
import statistics
import time
from hashlib import sha256
from pathlib import Path
from uuid import UUID

from luma.core.config import settings
from luma.core.database import database
from luma.features.catalog.retrieval import search_catalog
from luma.features.catalog.schemas import CatalogSearch
from psycopg.conninfo import conninfo_to_dict


def evaluate(company: UUID, output: Path):
    """Read only this local synthetic tenant, measure generated exact/descriptive Recall@5, and write credential-free evidence."""
    params = conninfo_to_dict(settings().luma_worker_database_url.get_secret_value())
    if params.get("host") not in ("127.0.0.1", "localhost") or params.get("port") != "55322":
        raise RuntimeError("Catalog evaluation requires this project's isolated local database.")
    with database(worker=True) as conn:
        tenant = conn.execute("select synthetic from luma.companies where id=%s", (company,)).fetchone()
        if not tenant or not tenant["synthetic"]:
            raise RuntimeError("Generated evaluation is restricted to an explicitly synthetic supplier.")
        products = conn.execute(
            """select p.* from luma.products p join luma.sources s on s.id=p.source_id and s.company_id=p.company_id
            where p.company_id=%s and not p.discontinued and s.retired_at is null order by p.sku limit 1000""",
            (company,),
        ).fetchall()
        if not products:
            raise RuntimeError("No current catalog products are available for evaluation.")
        cases = []
        durations = []
        for product in products:
            for kind, query in (
                ("exact", product["sku"]),
                (
                    "descriptive",
                    f"Please quote {product['family']} {product['watts']}W {product['cct']}K {product['ip_rating']}",
                ),
            ):
                start = time.perf_counter()
                hits = search_catalog(conn, company, CatalogSearch(query=query))
                durations.append((time.perf_counter() - start) * 1000)
                cases.append(
                    {
                        "kind": kind,
                        "query": query,
                        "expected_sku": product["sku"],
                        "retrieved_skus": [hit.sku for hit in hits],
                        "found": any(hit.sku == product["sku"] for hit in hits),
                    }
                )
    groups = {}
    for kind in ("exact", "descriptive"):
        selected = [case for case in cases if case["kind"] == kind]
        found = sum(case["found"] for case in selected)
        groups[kind] = {"cases": len(selected), "found": found, "recall_at_5": found / len(selected)}
    ordered = sorted(durations)
    report = {
        "scope": "Generated development baseline derived from current synthetic records; not the frozen 80-scenario evaluation or client validation",
        "method": "Exact-first PostgreSQL lexical search with explicit specification filters; no embeddings or model calls",
        "dataset_sha256": sha256(json.dumps(cases, sort_keys=True).encode()).hexdigest(),
        "groups": groups,
        "local_query_latency_ms": {
            "median": round(statistics.median(durations), 3),
            "p95": round(ordered[math.ceil(len(ordered) * 0.95) - 1], 3),
        },
        "cases": cases,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps({"groups": groups, "output": str(output), "scope": "generated development baseline only"})
    )
    if any(group["recall_at_5"] < 0.95 for group in groups.values()):
        raise SystemExit(1)


def main():
    """Require an explicit synthetic company target and evidence destination; never infer a live account."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", type=UUID, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evaluate(args.company, args.output)


if __name__ == "__main__":
    main()
