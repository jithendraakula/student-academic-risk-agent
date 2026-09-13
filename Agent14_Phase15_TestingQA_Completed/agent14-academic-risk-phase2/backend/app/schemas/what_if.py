from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class CourseWhatIf(BaseModel):
    course_id: str = Field(min_length=1, max_length=32)
    internal_marks: Optional[float] = Field(default=None, ge=0, le=100)
    midterm_marks: Optional[float] = Field(default=None, ge=0, le=100)
    quiz_average: Optional[float] = Field(default=None, ge=0, le=100)
    assignment_average: Optional[float] = Field(default=None, ge=0, le=100)
    practical_marks: Optional[float] = Field(default=None, ge=0, le=100)
    course_attendance_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    assignment_completion_rate: Optional[float] = Field(default=None, ge=0, le=1)


class WhatIfRequest(BaseModel):
    attendance_percentage: Optional[float] = Field(default=None, ge=0, le=100)
    gpa: Optional[float] = Field(default=None, ge=0, le=10)
    backlog_count: Optional[int] = Field(default=None, ge=0, le=30)
    assignment_completion_rate: Optional[float] = Field(default=None, ge=0, le=1)
    course: Optional[CourseWhatIf] = None

    @field_validator("assignment_completion_rate")
    @classmethod
    def round_rate(cls, value):
        return round(value, 4) if value is not None else value

    def has_change(self) -> bool:
        return any(value is not None for value in (
            self.attendance_percentage,
            self.gpa,
            self.backlog_count,
            self.assignment_completion_rate,
            self.course,
        ))
