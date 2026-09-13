# Remediation R13 — Production UX & Scalability Cleanup

## Goal

Clean the frontend for deployment-facing UX behavior without changing ML, risk, alert, intervention, notification, AI, or RBAC semantics.

## Changes

- Added a global Axios timeout and a 401 session-expiry redirect that clears client session state.
- Made authentication state restoration resilient to corrupt `sessionStorage` JSON.
- Added client-side pagination to Admin reference tables with a 50-row page size.
- Improved Admin search controls, responsive threshold form behavior, and record semantics.
- Added reduced-motion support to the institutional stylesheet.
- Removed confirmed-unused frontend boilerplate assets/components.
- Cleaned stale branding boilerplate references.
- Preserved the Vignan institutional visual system and existing role boundaries.

## Verification

- R13 static UX cleanup gate: PASS.
- Python compilation: PASS.
- R12/r11/r10/r9/r8/r7/r6/r5/r4/r3/r2/r1.5/r1/r0 and phase regressions are retained as the cumulative test baseline from prior verified phases.
- Full frontend Vite build remains environment-dependent and was not claimed as passed because the environment could not obtain the complete dependency/type cache.
