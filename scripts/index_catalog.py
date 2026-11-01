"""Explicit paid local synthetic catalog indexing; routine setup/tests never call this command."""

import argparse
import json
from uuid import UUID

from luma_agent.runtime.catalog_index import index_company


def main():
    """Require a company, stable operation UUID and explicit execution flag before an operator embedding batch."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--company", type=UUID, required=True)
    parser.add_argument("--run-id", type=UUID, required=True)
    parser.add_argument("--execute", action="store_true", required=True)
    args = parser.parse_args()
    print(json.dumps(index_company(args.company, args.run_id)))


if __name__ == "__main__":
    main()
