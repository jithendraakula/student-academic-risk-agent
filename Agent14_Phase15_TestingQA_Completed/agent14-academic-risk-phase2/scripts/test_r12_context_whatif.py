from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))
sys.path.insert(0, str(ROOT))

from app.services.context_intelligence import classify_observation, summarize_observations
from app.services.what_if import _apply_changes, _scenario_summary
from app.schemas.what_if import WhatIfRequest, CourseWhatIf


def obs(oid, text, category='attendance', follow=False, status='OPEN', date='2026-09-10'):
    return SimpleNamespace(id=oid, observation_text=text, category=category, follow_up_required=follow, status=status, observed_on=date, source_role='mentor')


def main():
    # Negation must not turn a negative statement into a health/assessment intent.
    assert classify_observation('health_related', 'Student does not have fever and reports no illness.')['intent'] == 'general_support'
    assert classify_observation('health_related', 'Fever is not present and the student is well.')['intent'] == 'general_support'
    assert classify_observation('assessment', 'Student did not miss the internal assessment.')['intent'] == 'general_support'

    # Specific context should beat generic category wording.
    health = classify_observation('attendance', 'Absent for two days due to fever and medical treatment.')
    assert health['intent'] == 'health_recovery'
    assert health['classifier'] == 'context_intent_v2'

    # Closed historical context should not become the primary action when a live
    # follow-up exists, even when the historical intent occurs more frequently.
    summary = summarize_observations([
        obs('old1', 'Student had repeated late arrival last month.', follow=False, status='CLOSED', date='2026-07-01'),
        obs('old2', 'Repeated late arrival was observed last month.', follow=False, status='CLOSED', date='2026-07-02'),
        obs('new1', 'Absent due to fever; mentor scheduled recovery follow-up.', category='health_related', follow=True, status='OPEN', date='2026-09-10'),
    ])
    assert summary['primary_context_intent'] == 'health_recovery', summary
    assert summary['active_follow_up_count'] == 1
    assert summary['active_observation_count'] == 1
    assert summary['method'] == 'context_intent_v2'

    # Assignment completion is independent from assessment participation.
    student = {
        'current_attendance_percentage': 78,
        'attendance_last_30_days': 78,
        'projected_final_attendance': 80,
        'assignment_completion_rate': 0.50,
        'assessment_participation_rate': 0.40,
        'current_gpa': 6.5,
        'previous_gpa': 6.5,
        'current_backlog_count': 1,
        'previous_backlog_count': 1,
        'repeated_backlog_subject_count': 0,
        'previous_backlog_count': 1,
    }
    adjusted, courses, changes = _apply_changes(
        student,
        [{'course_id': 'CSE101', 'course_name': 'Programming', 'internal_marks': 50, 'course_attendance_percentage': 65, 'assignment_completion_rate': 0.5}],
        WhatIfRequest(assignment_completion_rate=0.9),
    )
    assert adjusted['assignment_completion_rate'] == 0.9
    assert adjusted['assessment_participation_rate'] == 0.40
    assert changes['assignment_completion_rate']['unit'] == 'fraction'

    # Course assignment completion stays independent as well.
    course_payload = WhatIfRequest(course=CourseWhatIf(course_id='CSE101', assignment_completion_rate=0.9))
    _, adjusted_courses, course_changes = _apply_changes(student, [{'course_id': 'CSE101', 'assignment_completion_rate': 0.5}], course_payload)
    assert adjusted_courses[0]['assignment_completion_rate'] == 0.9
    assert course_changes['course']['fields']['assignment_completion_rate']['note'] == 'Independent from assessment participation'

    scenario = _scenario_summary(changes)
    assert scenario['mode'] == 'single_factor'
    assert scenario['factor_count'] == 1
    print('R12 context/what-if refinement tests: PASS')


if __name__ == '__main__':
    main()
