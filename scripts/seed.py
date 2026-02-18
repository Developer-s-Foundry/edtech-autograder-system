# scripts/seed.py
"""
Ticket 1.2 - Seed Script for Demo Data

Creates:
- 1 instructor
- 2 students
- 1 assignment
- 3 IO test cases
- 1 unit test spec
- 1 static rules config

Rerunnable safely (idempotent):
- Uses unique email for users
- Uses (instructor_id, title) for assignment lookup
- Uses (assignment_id, name) for IO test cases lookup
- Uses assignment_id unique constraint for unit_test_spec + static_rules
"""

from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime

# Ensure project root is in PYTHONPATH when running: python scripts/seed.py
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from sqlalchemy import select
from passlib.context import CryptContext
from app.db import SessionLocal
from app.models.models import User, Assignment, IOTestCase, UnitTestSpec, StaticRule


# -----------------------------
# Seed constants (demo values)
# -----------------------------
INSTRUCTOR_EMAIL = "instructor.demo@autograder.local"
STUDENT1_EMAIL = "student1.demo@autograder.local"
STUDENT2_EMAIL = "student2.demo@autograder.local"

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
DEMO_PASSWORD = "demo_password_123"
DEMO_PASSWORD_HASH = _pwd_context.hash(DEMO_PASSWORD)

ASSIGNMENT_TITLE = "MVP Demo - Add Two Numbers"
ASSIGNMENT_DESCRIPTION = (
    "Write a Python function solve() that reads two integers from stdin and prints their sum.\n\n"
    "Input: two integers separated by space\n"
    "Output: sum of the two integers\n"
)
ASSIGNMENT_INSTRUCTIONS = (
    "Requirements:\n"
    "1) Implement solve()\n"
    "2) Use input() to read values\n"
    "3) Print output only (no extra text)\n"
)


def get_or_create_user(db, *, email: str, role: str, full_name: str) -> User:
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user:
        # keep seed stable but ensure critical fields exist
        user.role = role
        user.full_name = full_name
        user.is_active = True
        if not user.password_hash:
            user.password_hash = DEMO_PASSWORD_HASH
        return user

    user = User(
        email=email,
        password_hash=DEMO_PASSWORD_HASH,
        role=role,
        full_name=full_name,
        is_active=True,
    )
    db.add(user)
    db.flush()
    return user


def get_or_create_assignment(db, *, instructor_id: int) -> Assignment:
    assignment = db.execute(
        select(Assignment).where(
            Assignment.instructor_id == instructor_id,
            Assignment.title == ASSIGNMENT_TITLE,
        )
    ).scalar_one_or_none()

    if assignment:
        # Update to ensure demo is fully configured
        assignment.description = ASSIGNMENT_DESCRIPTION
        assignment.instructions = ASSIGNMENT_INSTRUCTIONS
        assignment.language = "python"
        assignment.is_published = True
        assignment.weight_io = 70
        assignment.weight_unit = 20
        assignment.weight_static = 10
        assignment.max_runtime_ms = 2000
        assignment.max_memory_kb = 128000
        return assignment

    assignment = Assignment(
        instructor_id=instructor_id,
        title=ASSIGNMENT_TITLE,
        description=ASSIGNMENT_DESCRIPTION,
        instructions=ASSIGNMENT_INSTRUCTIONS,
        language="python",
        is_published=True,
        weight_io=70,
        weight_unit=20,
        weight_static=10,
        max_runtime_ms=2000,
        max_memory_kb=128000,
    )
    db.add(assignment)
    db.flush()
    return assignment


def get_or_create_io_test_case(
    db, *, assignment_id: int, name: str, stdin: str | None, expected_stdout: str, points: int, is_hidden: bool, order_index: int
) -> IOTestCase:
    tc = db.execute(
        select(IOTestCase).where(IOTestCase.assignment_id == assignment_id, IOTestCase.name == name)
    ).scalar_one_or_none()

    if tc:
        tc.stdin = stdin
        tc.expected_stdout = expected_stdout
        tc.points = points
        tc.is_hidden = is_hidden
        tc.order_index = order_index
        return tc

    tc = IOTestCase(
        assignment_id=assignment_id,
        name=name,
        stdin=stdin,
        expected_stdout=expected_stdout,
        points=points,
        is_hidden=is_hidden,
        order_index=order_index,
    )
    db.add(tc)
    db.flush()
    return tc


def get_or_create_unit_test_spec(db, *, assignment_id: int) -> UnitTestSpec:
    spec = db.execute(select(UnitTestSpec).where(UnitTestSpec.assignment_id == assignment_id)).scalar_one_or_none()

    test_code = (
        "def run_tests():\n"
        "    # basic asserts - keep hidden tests hidden\n"
        "    assert solve_from_values(2, 3) == 5\n"
        "    assert solve_from_values(-1, 1) == 0\n"
        "    assert solve_from_values(100, 200) == 300\n"
        "\n"
        "# helper to test student logic without stdin\n"
        "def solve_from_values(a, b):\n"
        "    return a + b\n"
        "\n"
        "run_tests()\n"
    )

    # For MVP demo: we store an assert block.
    # Later, your unit harness will wrap student code + these asserts properly.

    if spec:
        spec.name = "Unit Tests - Add Two Numbers"
        spec.test_code = test_code
        spec.points = 20
        spec.is_hidden = True
        return spec

    spec = UnitTestSpec(
        assignment_id=assignment_id,
        name="Unit Tests - Add Two Numbers",
        test_code=test_code,
        points=20,
        is_hidden=True,
    )
    db.add(spec)
    db.flush()
    return spec


def get_or_create_static_rules(db, *, assignment_id: int) -> StaticRule:
    rules = db.execute(select(StaticRule).where(StaticRule.assignment_id == assignment_id)).scalar_one_or_none()

    required_functions = ["solve"]
    forbidden_imports = ["os", "sys", "subprocess"]

    if rules:
        rules.required_functions = required_functions
        rules.forbidden_imports = forbidden_imports
        rules.max_cyclomatic_complexity = 5
        rules.points = 10
        return rules

    rules = StaticRule(
        assignment_id=assignment_id,
        required_functions=required_functions,
        forbidden_imports=forbidden_imports,
        max_cyclomatic_complexity=5,
        points=10,
    )
    db.add(rules)
    db.flush()
    return rules


def main():
    db = SessionLocal()
    try:
        # Users
        instructor = get_or_create_user(
            db,
            email=INSTRUCTOR_EMAIL,
            role="instructor",
            full_name="Demo Instructor",
        )
        student1 = get_or_create_user(
            db,
            email=STUDENT1_EMAIL,
            role="student",
            full_name="Demo Student One",
        )
        student2 = get_or_create_user(
            db,
            email=STUDENT2_EMAIL,
            role="student",
            full_name="Demo Student Two",
        )

        # Assignment
        assignment = get_or_create_assignment(db, instructor_id=instructor.id)

        # IO test cases (3)
        get_or_create_io_test_case(
            db,
            assignment_id=assignment.id,
            name="IO Test 1 - small positives",
            stdin="2 3\n",
            expected_stdout="5\n",
            points=30,
            is_hidden=False,
            order_index=1,
        )
        get_or_create_io_test_case(
            db,
            assignment_id=assignment.id,
            name="IO Test 2 - negatives",
            stdin="-5 2\n",
            expected_stdout="-3\n",
            points=20,
            is_hidden=True,
            order_index=2,
        )
        get_or_create_io_test_case(
            db,
            assignment_id=assignment.id,
            name="IO Test 3 - larger numbers",
            stdin="100 200\n",
            expected_stdout="300\n",
            points=20,
            is_hidden=True,
            order_index=3,
        )

        # Unit Test Spec (1)
        get_or_create_unit_test_spec(db, assignment_id=assignment.id)

        # Static Rules (1)
        get_or_create_static_rules(db, assignment_id=assignment.id)

        db.commit()

        print("✅ Seed completed successfully.")
        print(f"   Instructor: {instructor.email}")
        print(f"   Students:   {student1.email}, {student2.email}")
        print(f"   Assignment: {assignment.title} (published={assignment.is_published})")

    except Exception as e:
        db.rollback()
        print("❌ Seed failed:", str(e))
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
