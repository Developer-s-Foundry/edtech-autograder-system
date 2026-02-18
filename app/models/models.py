from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

from app.models.base import Base


# -------------------------
# Enums
# -------------------------
class UserRole(str, Enum):
    student = "student"
    instructor = "instructor"


class SubmissionStatus(str, Enum):
    queued = "queued"
    running = "running"
    completed = "completed"
    failed = "failed"


class GradingRunStatus(str, Enum):
    running = "running"
    completed = "completed"
    failed = "failed"


# -------------------------
# Users
# -------------------------
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # keep simple, validate in app layer
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships (cardinality)
    assignments: Mapped[list["Assignment"]] = relationship("Assignment", back_populates="instructor")
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="student")

    __table_args__ = (
        CheckConstraint("role IN ('student', 'instructor')", name="ck_users_role"),
    )


# -------------------------
# Assignments
# -------------------------
class Assignment(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    instructor_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)

    language: Mapped[str] = mapped_column(String(50), default="python", nullable=False)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    weight_io: Mapped[int] = mapped_column(Integer, default=70, nullable=False)
    weight_unit: Mapped[int] = mapped_column(Integer, default=20, nullable=False)
    weight_static: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    max_runtime_ms: Mapped[int] = mapped_column(Integer, default=2000, nullable=False)
    max_memory_kb: Mapped[int] = mapped_column(Integer, default=128000, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    instructor: Mapped["User"] = relationship("User", back_populates="assignments")
    io_test_cases: Mapped[list["IOTestCase"]] = relationship("IOTestCase", back_populates="assignment")
    unit_test_spec: Mapped["UnitTestSpec | None"] = relationship("UnitTestSpec", back_populates="assignment", uselist=False)
    static_rule: Mapped["StaticRule | None"] = relationship("StaticRule", back_populates="assignment", uselist=False)
    submissions: Mapped[list["Submission"]] = relationship("Submission", back_populates="assignment")

    __table_args__ = (
        CheckConstraint("weight_io >= 0 AND weight_unit >= 0 AND weight_static >= 0", name="ck_assignment_weights_nonneg"),
        CheckConstraint("(weight_io + weight_unit + weight_static) = 100", name="ck_assignment_weights_sum_100"),
    )


# -------------------------
# IO Test Cases
# -------------------------
class IOTestCase(Base):
    __tablename__ = "io_test_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    stdin: Mapped[str | None] = mapped_column(Text, nullable=True)
    expected_stdout: Mapped[str] = mapped_column(Text, nullable=False)

    points: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="io_test_cases")
    test_case_results: Mapped[list["TestCaseResult"]] = relationship("TestCaseResult", back_populates="io_test_case")


# -------------------------
# Unit Test Specs (0..1 per assignment)
# -------------------------
class UnitTestSpec(Base):
    __tablename__ = "unit_test_specs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    test_code: Mapped[str] = mapped_column(Text, nullable=False)  # asserts only
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="unit_test_spec")


# -------------------------
# Static Rules (0..1 per assignment)
# -------------------------
class StaticRule(Base):
    __tablename__ = "static_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    required_functions: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    forbidden_imports: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    max_cyclomatic_complexity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    points: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="static_rule")


# -------------------------
# Submissions
# -------------------------
class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True, nullable=False)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    code_text: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[str] = mapped_column(String(20), default=SubmissionStatus.queued.value, nullable=False)

    # IMPORTANT: circular-ish pointer to grading_runs (latest)
    latest_grading_run_id: Mapped[int | None] = mapped_column(
        ForeignKey("grading_runs.id", ondelete="SET NULL", use_alter=True, name="fk_submissions_latest_grading_run"),
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="submissions")
    student: Mapped["User"] = relationship("User", back_populates="submissions")

    grading_runs: Mapped[list["GradingRun"]] = relationship("GradingRun", 
                    back_populates="submission", foreign_keys="[GradingRun.submission_id]",)

    latest_grading_run: Mapped["GradingRun | None"] = relationship(
        "GradingRun",
        foreign_keys=[latest_grading_run_id],
        post_update=True,  # helps SQLAlchemy handle this pointer
    )

    __table_args__ = (
        CheckConstraint("status IN ('queued', 'running', 'completed', 'failed')", name="ck_submissions_status"),
    )


# -------------------------
# Grading Runs
# -------------------------
class GradingRun(Base):
    __tablename__ = "grading_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), index=True, nullable=False)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default=GradingRunStatus.running.value, nullable=False)

    io_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unit_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    static_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    judge0_io_tokens: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    judge0_unit_token: Mapped[str | None] = mapped_column(Text, nullable=True)

    feedback_summary: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ai_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)

    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    submission: Mapped["Submission"] = relationship("Submission", back_populates="grading_runs",
                                                    foreign_keys=[submission_id],)
    test_case_results: Mapped[list["TestCaseResult"]] = relationship("TestCaseResult", back_populates="grading_run")
    static_analysis_report: Mapped["StaticAnalysisReport | None"] = relationship(
        "StaticAnalysisReport",
        back_populates="grading_run",
        uselist=False
    )

    __table_args__ = (
        CheckConstraint("status IN ('running', 'completed', 'failed')", name="ck_grading_runs_status"),
    )


# -------------------------
# Test Case Results
# -------------------------
class TestCaseResult(Base):
    __tablename__ = "test_case_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grading_run_id: Mapped[int] = mapped_column(ForeignKey("grading_runs.id", ondelete="CASCADE"), index=True, nullable=False)
    io_test_case_id: Mapped[int] = mapped_column(ForeignKey("io_test_cases.id", ondelete="CASCADE"), index=True, nullable=False)

    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    points_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    grading_run: Mapped["GradingRun"] = relationship("GradingRun", back_populates="test_case_results")
    io_test_case: Mapped["IOTestCase"] = relationship("IOTestCase", back_populates="test_case_results")

    __table_args__ = (
        UniqueConstraint("grading_run_id", "io_test_case_id", name="uq_test_case_results_run_case"),
    )


# -------------------------
# Static Analysis Reports (0..1 per grading run)
# -------------------------
class StaticAnalysisReport(Base):
    __tablename__ = "static_analysis_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    grading_run_id: Mapped[int] = mapped_column(ForeignKey("grading_runs.id", ondelete="CASCADE"), unique=True, index=True, nullable=False)

    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    violations: Mapped[list[dict] | None] = mapped_column(JSONB, nullable=True)

    cyclomatic_complexity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    radon_report: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    grading_run: Mapped["GradingRun"] = relationship("GradingRun", back_populates="static_analysis_report")
