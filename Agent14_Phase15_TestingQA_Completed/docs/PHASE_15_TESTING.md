# Phase 15 — Testing & QA

Phase 15 is the cumulative QA gate before deployment. It verifies the five canonical risk types, priority/alert policy, processed data contract, ML predictor contract, institutional role workflows, intervention lifecycle, What-If simulation, grounded AI boundaries, notification behavior, security controls, and the frontend institutional branding contract.

## Fast QA

The dependency-light gate is:

```text
python scripts/test_phase15_qa.py
```

It validates Python syntax, processed-data counts/schema, canonical risk/priority policy, frontend package/branding/workflow contract, the Phase 1 validator, and the ML smoke test.

## Full QA

The cumulative endpoint suite can be run with:

```text
python scripts/test_phase15_qa.py --full
```

Each phase API test gets a fresh SQLite database and the generated test databases are deleted after the run. Phase 11 institutional AI is intentionally given a longer timeout because it materializes the canonical current-risk store for scoped analysis.

## Report

The latest fast/full run writes:

```text
test_artifacts/phase15_report.json
```

## Release gate

Before Phase 16 deployment, the target environment must also complete `npm ci && npm run build`, real provider-specific LLM smoke tests (with deployment credentials), and real SMTP delivery testing. Those external services are not contacted by the offline QA suite.

## QA principle

A test that was not actually run is not marked as passed. Environment or dependency limitations are recorded separately from verified application behavior.


## R9 follow-up gate

`python scripts/test_r9_runtime_alerts.py` validates live alert/work-item semantics against a fresh runtime database. The seed CSV count is not treated as the production KPI.
