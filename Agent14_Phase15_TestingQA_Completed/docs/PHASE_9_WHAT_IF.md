# Phase 9 — What-If Simulator

## Purpose

Provide mentors, HODs, and the Dean with a safe academic scenario simulator. The user can change attendance, GPA, backlog count, assignment completion, or selected course performance and see how the existing ML risks and canonical priorities would change.

## Safety / architecture

What-if runs are **non-persistent**. The simulator clones the latest current semester feature snapshot in memory, applies the requested scenario, calls the existing trained models, and calculates priority from the canonical priority engine. It never writes `Student`, feature tables, `RiskPrediction`, alerts, or intervention history.

The simulator is for decision support only. Its output does not become official academic history until real academic data are updated through the appropriate institutional workflow and a normal prediction refresh occurs.

## Supported scenarios

- Student attendance percentage
- Student current GPA
- Current backlog count
- Assignment completion rate
- Selected course: internal marks, midterm marks, quiz, assignment, practical, course attendance, assignment completion

## API

`POST /api/what-if/student/{student_id}`

Roles: `mentor`, `hod`, `dean`

Example:

```json
{
  "attendance_percentage": 88,
  "gpa": 8.2,
  "backlog_count": 0,
  "assignment_completion_rate": 0.95
}
```

Course example:

```json
{
  "course": {
    "course_id": "CSE101",
    "internal_marks": 90,
    "midterm_marks": 88,
    "quiz_average": 92,
    "assignment_average": 90,
    "practical_marks": 90,
    "course_attendance_percentage": 92,
    "assignment_completion_rate": 1.0
  }
}
```

## Interpretation

The response includes baseline and simulated risk/priority values, per-risk deltas, primary risk, and an explicit `persistent: false` marker plus a warning that the result is an estimate.
