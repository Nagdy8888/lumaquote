# Synthetic development confirmation cases

`inputs.json` contains 40 neutral case IDs, customer message histories (newest
first), modality labels and deliberately controlled untrusted extraction output.
`oracle.json` is an evaluator-only mapping from those IDs to a hand-specified
action and reason. Both live outside application code, catalog/Storage ingestion,
prompts and traces. Runtime modules must never import or ingest these files.
No customer names, real media or client records are used.

This development corpus covers 20 text, 12 voice-policy and 8 photo-policy
specifications. Voice/photo observations are **controlled text substitutes**,
not recordings or recognition results. The suite tests missing, invented,
mismatched, repeated and uncertain fields; negation; cancellation; alternatives;
conditional compatibility; unit confusion; injected authority; media-only input;
and valid complete written confirmations. The oracle grants `fields_confirmed`
only: it does not mean a supported catalog line, successful quote or authorized
send. The fixtures intentionally include well-formed but incorrect model outputs
to test the boundary rather than trusting provider correctness.

Run `node scripts/python.cjs -m pytest tests/unit/test_written_requests.py -q`.
The pytest suite compares deterministic actions and fixed question wording,
checks oracle completeness/modality denominators, and adds generated numeric
boundaries plus invalid-form/list-limit checks. It contacts no provider or
database. Existing real-database graph tests separately establish that denied
requests remain paused without a quote and complete restatements can resume.

These 40 specifications are **not** the planned frozen 80-case evaluation, a
60/20 split, a holdout, acoustic/vision quality, retrieval recall or end-to-end
workflow accuracy. No holdout has been consumed by this corpus. Realistic noisy
recordings, unclear labels, split-by-family release fixtures, code/config freeze
and independent staff review remain required by [the testing plan](../../../docs/TESTING_PLAN.md).
When a failure drives a policy change, retain the case and its independent
business rationale; do not rewrite the oracle simply to match implementation.
