# Phase 13 — UI/UX

## Goal
Bring the full application to a coherent college/institutional visual system using the supplied Vignan's University reference as the visual source.

## Visual direction
- Institutional white + navy/academic blue surfaces.
- Pale blue backgrounds for active states and information areas.
- Restrained red/orange/amber/green reserved for risk severity.
- Compact administrative data density with readable tables.
- Consistent rounded cards, fine borders, subtle shadows and restrained typography.
- Reference-derived Vignan's University mark and accreditation/NIRF-style badge row are stored under `frontend/public/branding/`.

## Shared shell
`InstitutionalShell.tsx` now provides the common top institutional masthead, accreditation row, role identity, navigation, notification access for staff roles, responsive mobile treatment and institutional footer.

## Role workspaces
Mentor, HOD, Dean, Admin and Student Profile now inherit the same shell and visual language. The content hierarchy remains role-specific: student action for Mentor, department oversight for HOD, institution oversight for Dean and configuration/governance for Admin.

## AI visual treatment
AI analyst panels are presented as grounded academic tooling and explicitly distinguish canonical data from generated interpretation.

## Verification note
The frontend production build could not be completed in the current offline runtime because the available `node_modules` installation is incomplete (`vite/client` and Node type definitions are unavailable). Source-level edits were kept dependency-free and backend behavior was not changed in Phase 13.
