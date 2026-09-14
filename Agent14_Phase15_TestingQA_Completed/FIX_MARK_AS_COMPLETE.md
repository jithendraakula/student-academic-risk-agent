# Mark as Complete Fix

## What was fixed
1. The Mentor Attention Queue now synchronizes canonical actionable risk predictions into intervention records before filtering.
2. Existing manually resolved alerts tied to the current prediction remain `RESOLVED`, so refreshes do not recreate the same task.
3. `Mark as complete` is shown for every student row that has an open intervention record, not only when the row's `needs_action` summary is true.
4. The completion action continues to use the authenticated mentor intervention PATCH endpoint and refreshes the queue/metrics after success.
5. The button remains unavailable while its request is in progress to prevent duplicate clicks.

## Validation
- Backend `compileall`: passed.
- Static checks for synchronization and completion rendering: passed.
- Full frontend Vite build was not available in this runtime because the archive does not contain installed frontend packages (`vite`/`tsc`).
