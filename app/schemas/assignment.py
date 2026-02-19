from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import Optional


class AssignmentBase(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=1)
    instructions: Optional[str] = None

    language: str = Field(default="python", max_length=50)
    is_published: bool = False

    weight_io: int = Field(default=70, ge=0, le=100)
    weight_unit: int = Field(default=20, ge=0, le=100)
    weight_static: int = Field(default=10, ge=0, le=100)

    max_runtime_ms: int = Field(default=2000, ge=100, le=600000)
    max_memory_kb: int = Field(default=128000, ge=16000, le=2000000)

    @model_validator(mode="after")
    def validate_weights_sum(self):
        total = self.weight_io + self.weight_unit + self.weight_static
        if total != 100:
            raise ValueError("weight_io + weight_unit + weight_static must equal 100")
        return self


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentUpdate(BaseModel):
    # all optional for PUT update
    title: Optional[str] = Field(default=None, min_length=3, max_length=255)
    description: Optional[str] = None
    instructions: Optional[str] = None

    language: Optional[str] = Field(default=None, max_length=50)
    is_published: Optional[bool] = None

    weight_io: Optional[int] = Field(default=None, ge=0, le=100)
    weight_unit: Optional[int] = Field(default=None, ge=0, le=100)
    weight_static: Optional[int] = Field(default=None, ge=0, le=100)

    max_runtime_ms: Optional[int] = Field(default=None, ge=100, le=600000)
    max_memory_kb: Optional[int] = Field(default=None, ge=16000, le=2000000)

    @model_validator(mode="after")
    def validate_weights_sum_if_any(self):
        # Only validate sum if any weight is being updated
        weights = [self.weight_io, self.weight_unit, self.weight_static]
        if any(w is not None for w in weights):
            # Caller must provide all three weights if changing weights
            if any(w is None for w in weights):
                raise ValueError("If updating weights, provide weight_io, weight_unit, and weight_static")
            total = self.weight_io + self.weight_unit + self.weight_static
            if total != 100:
                raise ValueError("weight_io + weight_unit + weight_static must equal 100")
        return self


class AssignmentOut(AssignmentBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instructor_id: int


class StudentAssignmentOut(BaseModel):
    """
    Stripped-down assignment view for students.
    Excludes: instructor_id, is_published, max_runtime_ms, max_memory_kb,
    and all test case / grading rule definitions.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    instructions: Optional[str]
    language: str
    weight_io: int
    weight_unit: int
    weight_static: int
    created_at: datetime
    updated_at: datetime
