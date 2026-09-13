# Remediation R6 — Cross-Role UX & Responsive Scalability

## Goal
Make Mentor, HOD, Dean and Admin behave like one coherent institutional application across desktop, tablet and mobile widths, with predictable spacing, readable data tables, accessible navigation and bounded overlays.

## UX principles
- 8px spacing rhythm and bounded content widths.
- `min-w-0` on grid/flex children so dynamic content can shrink instead of forcing overflow.
- Tables remain data-dense but become horizontally scrollable on narrow screens rather than crushing columns.
- Loading is represented as loading, never as a misleading zero state.
- Navigation remains usable at narrow widths through horizontal scrolling.
- Notification overlays are viewport-bounded and closable with Escape or outside click.
- Vignan institutional branding remains the visual authority.

## Scope
- Institutional shell/header/navigation
- Notification placement and keyboard/pointer dismissal
- Tables and mobile overflow treatment
- Shared cards/workspace intro sizing
- Mentor/HOD/Dean/Admin responsive grids and loading semantics
- Login typography scaling

## Explicit non-goals
This phase does not change risk calculations, database semantics, RBAC scope, ML models, AI behavior, or notification policy.
