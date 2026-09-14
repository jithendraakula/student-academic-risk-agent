# Mark as Complete — Final Workflow Fix

## What changed

1. **Mentor queue**
   - Every student row now has a `Mark as complete` button.
   - The button no longer depends on the row having one specific `primary_alert`.
   - Clicking it completes the **whole student case**.

2. **Whole-case completion**
   - A single completion request resolves every currently open intervention for that student.
   - The completion is persisted in the database.
   - Intervention history and audit records are written for each resolved alert.
   - If a student has no open intervention, a persisted resolved case-completion marker is recorded so the action is still durable.

3. **Student profile**
   - The mentor can complete the student case from the profile.
   - Completion uses the same student-level endpoint as the queue, avoiding different behavior between the two screens.
   - The profile refreshes after completion so open work becomes zero.

4. **Dashboard KPI refresh**
   - Mentor, HOD, and Dean dashboards listen for case-work updates.
   - Updates refresh in the same tab immediately.
   - A local-storage signal also refreshes open dashboards in another browser tab.
   - `Needs action` is now tied to students who both need action from the risk model and still have open case work. Therefore completing the case reduces the operational `Needs action` count while risk severity metrics (Critical/High) remain the risk-model truth.

## Validation

- Backend `compileall` passed.
- Direct SQLAlchemy integration test passed: a test student with two open interventions had both resolved and both intervention-history records created.
- Frontend full Vite build could not be completed in this environment because the supplied archive does not have `vite/client` and `@types/node` installed in `node_modules`. Run `npm install` and then `npm run build` locally.
