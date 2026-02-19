from pydantic import BaseModel, Field, ConfigDict
from typing import Optional


class UnitTestSpecUpsert(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    test_code: str = Field(min_length=1)  # assert statements only (validated later in grading)
    points: int = Field(default=0, ge=0, le=100000)
    is_hidden: bool = True


class UnitTestSpecOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    name: str
    test_code: str
    points: int
    is_hidden: bool
