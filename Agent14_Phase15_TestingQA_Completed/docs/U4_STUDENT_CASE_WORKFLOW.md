# U4 — Student Academic Case Workflow

The student record is presented as a faculty-only academic support case, not as a student-facing dashboard.

The case hierarchy is:

1. Student identity and academic cycle.
2. Primary current status: canonical risk + priority.
3. Current academic position.
4. Risk evidence and underlying measures.
5. Faculty context and system interpretation.
6. Decision support.
7. Active support work.
8. Course review.
9. What-If and Mentor AI for mentors.

The page displays roll number, semester, and academic year. Risk probability, risk score, and priority are explicitly separated. Existing ML factors are used when supplied; otherwise the page displays the underlying academic measure rather than `No factor supplied`.

Students are never application users; the page is accessible only through the existing authority-scoped RBAC routes.
