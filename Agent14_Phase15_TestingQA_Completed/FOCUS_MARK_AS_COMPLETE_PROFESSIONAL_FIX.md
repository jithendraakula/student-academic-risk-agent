# Mark as Complete — Professional Workflow Fix

- Completion is persisted in `alerts_interventions` and `intervention_records`.
- Mentor queue and Mentor student profile both use the same student-case completion endpoint.
- Completion resolves all currently open alerts for the student in one transaction.
- A durable `case_completion` marker makes the completion state survive refresh/re-login and prevents duplicate completion records.
- If a newer open risk alert is generated after completion, the case becomes active again automatically.
- Mentor/HOD/Dean refresh from the database immediately after the local completion event and poll every 15 seconds for cross-user updates.
- Admin has a database-backed case summary with open and completed case totals.
- Expected permission/validation failures return proper HTTP errors instead of silent 500s.
