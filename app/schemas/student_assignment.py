from pydantic import BaseModel, ConfigDict
from typing import Optional


class StudentAssignmentListOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    language: str
    is_published: bool


class StudentAssignmentDetailOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    instructions: Optional[str]

    language: str

    weight_io: int
    weight_unit: int
    weight_static: int

    max_runtime_ms: int
    max_memory_kb: int
