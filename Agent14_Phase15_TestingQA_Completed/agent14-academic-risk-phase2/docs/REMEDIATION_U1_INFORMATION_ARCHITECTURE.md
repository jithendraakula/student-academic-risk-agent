# U1 — Faculty Flow & Information Architecture

## Objective
Establish one role-aware faculty workflow before detailed visual-system work. The application remains restricted to mentors, HODs, the dean, and other verified authorities; students are academic records, not application users.

## Locked role flows

### Mentor
Review attention queue → Open student case → Record support action

### HOD
Review CSE department status → Compare mentor support demand → Open student case

### Dean
Review institutional status → Identify priority area → Review authorized case

### Admin
Review configuration → Review authority/academic records → Apply policy changes

## Information hierarchy

Mentor workspaces lead with the attention queue; summary metrics follow as context. HOD workspaces lead from department summary to mentor oversight, student review, risk profile, and institutional AI. Dean workspaces lead from institutional priority to department comparison, authorized student review, risk distribution/concentration, and institutional AI.

The student profile is referred to as a **Student case** in navigation. It is an authorized faculty review flow, not a student-facing portal.

## Content rules introduced in U1
- Avoid backend/entity terminology in primary workflow UI (for example `risk_predictions`).
- Primary workspace copy should describe faculty tasks, not explain implementation architecture.
- Role-inappropriate AI controls remain hidden.
- Canonical risk type uses `support_attention` in frontend filters.
- Detailed visual styling remains aligned to the existing Vignan institutional theme; U1 changes information order and labels, not the locked brand palette.

## Exit criteria
A first-time authorized user should be able to identify the main task on the current workspace without needing to understand ML, priority-engine, alert-policy, or database terminology.
