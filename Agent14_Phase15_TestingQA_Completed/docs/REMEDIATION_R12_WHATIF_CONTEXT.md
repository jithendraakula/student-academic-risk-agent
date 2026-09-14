# Remediation R12 — What-If & Context Intelligence Refinement

## Goal
Make textual academic context more reliable and make What-If scenarios academically interpretable without changing real student records.

## Context intelligence v2
- Uses cue groups plus category agreement rather than exact full-text matching.
- Rejects common negation traps such as "does not have fever" and "did not miss the assessment".
- Surfaces ambiguity and evidence basis.
- Prioritizes active/open and follow-up observations, with recent observations ahead of old history.
- Closed observations remain visible as history but are not preferred for new alert routing.

## What-If rules
- Scenarios are non-persistent.
- A global assignment-completion change changes only assignment completion; it does not fabricate assessment participation.
- Course scenarios target one measurable course factor at a time in the UI.
- Current course values are supplied from the current course snapshot.
- Results identify the scenario factor and make the non-persistence warning explicit.

## AI boundary
The context layer is deterministic and auditable. LLMs may explain structured context and What-If results, but they do not create numerical risk scores.
