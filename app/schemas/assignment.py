from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AssignmentCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    instructions: Optional[str] = None
    language: str = Field(default="python", max_length=50)
    is_published: bool = False
    weight_io: int = Field(..., ge=0)
    weight_unit: int = Field(..., ge=0)
    weight_static: int = Field(..., ge=0)
    max_runtime_ms: int = Field(..., gt=0)
    max_memory_kb: int = Field(..., gt=0)

    @model_validator(mode="after")
    def weights_sum_to_100(self) -> "AssignmentCreate":
        total = self.weight_io + self.weight_unit + self.weight_static
        if total != 100:
            raise ValueError(
                f"weight_io + weight_unit + weight_static must equal 100, got {total}"
            )
        return self


class AssignmentUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    instructions: Optional[str] = None
    language: Optional[str] = Field(None, max_length=50)
    is_published: Optional[bool] = None
    weight_io: Optional[int] = Field(None, ge=0)
    weight_unit: Optional[int] = Field(None, ge=0)
    weight_static: Optional[int] = Field(None, ge=0)
    max_runtime_ms: Optional[int] = Field(None, gt=0)
    max_memory_kb: Optional[int] = Field(None, gt=0)


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    instructor_id: int
    title: str
    description: str
    instructions: Optional[str]
    language: str
    is_published: bool
    weight_io: int
    weight_unit: int
    weight_static: int
    max_runtime_ms: int
    max_memory_kb: int
    created_at: datetime
    updated_at: datetime
