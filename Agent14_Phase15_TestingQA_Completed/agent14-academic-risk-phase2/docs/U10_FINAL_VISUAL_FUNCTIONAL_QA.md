# U10 — Final Visual & Functional QA

## Scope
Final pre-deployment verification of the faculty-facing CSE academic support application after U1–U9.

## Product invariant
The application is for verified Mentor, HOD, Dean and other authorized institutional users. Students are records, not application users.

## Visual QA focus
- Vignan institutional navy/blue, white and pale-blue visual language retained.
- Risk colors remain semantic and restrained.
- Page-level horizontal overflow prevented; wide tables may scroll inside their containers.
- Shared button, icon, card and section-heading rules retained.
- Loading, empty and error states preserved.
- Notification action center remains above page content.

## Functional QA focus
- Mentor risk/priority labels are distinct.
- Non-actionable students are presented as Monitor rather than intervention targets.
- Student profile uses canonical backend status values.
- Mentor-only AI controls are role-gated.
- HOD section filters are derived from the selected mentor.
- Session-expiry handling is global.
- Production secrets remain excluded.

## Verified in this environment
- U10 final QA: 14/14 checks passed.
- Phase 15 fast QA passed.
- R15 integration passed.
- U8 responsive UX: 12/12 passed.
- U9 microcopy gate passed.
- Frontend TS/TSX transpile: 27/27 files, no diagnostics.
- Backend/ML/script Python AST syntax: passed.

## Not verified here
- Full production Vite build with installed dependencies.
- Live Gemini/xAI request with production credentials.
- Live SMTP delivery.
- Pixel-perfect browser rendering across every physical viewport; source-level responsive checks and structural QA were completed.
