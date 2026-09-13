# Remediation R8 — Academic Data & Timeline Integrity

## Goal

Correct the academic-year mapping for the 2024-entry CSE demo cohort and ensure the generated, processed, and runtime-facing datasets tell one consistent academic story.

## Correct timeline

| Semester | Academic year | Status |
|---|---|---|
| 1 | 2024-25 | Historical |
| 2 | 2024-25 | Historical |
| 3 | 2025-26 | Historical |
| 4 | 2025-26 | Historical |
| 5 | 2026-27 | Current |

The active student master record and current mentor assignments therefore use `2026-27` and semester `5`.

## Why this matters

The old generator advanced the academic year on every semester, which incorrectly placed semester 4 and semester 5 in future academic years. That made the student master, semester snapshots, historical outcomes, and the current application state disagree about when the cohort actually is.

## Changes

- Fixed `academic_year_for_semester()` to map two semesters per academic year.
- Regenerated all processed datasets from the canonical generator.
- Bumped the dataset manifest to `agent14-cse-2026-r8`.
- Added `scripts/test_r8_data_timeline.py`.
- Updated the R1 regression gate to accept the current R8 dataset version while retaining backward compatibility with an original R1 dataset.
- Updated project documentation to record the corrected timeline.

## Verification

R8 timeline gate verifies:

- active cohort is semester 5 / academic year 2026-27
- semester 1-2 map to 2024-25
- semester 3-4 map to 2025-26
- historical outcomes use the matching historical year
- course snapshots use the matching year
- every student has exactly semesters 1-5
- no future academic years appear in the processed timeline
- the dataset remains CSE-only

The ML feature set explicitly excludes `academic_year`, so correcting the labels does not change the trained model inputs. Existing R1 model metrics were rechecked after regeneration.
