from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List


class StaticRuleUpsert(BaseModel):
    required_functions: Optional[List[str]] = None
    forbidden_imports: Optional[List[str]] = None
    max_cyclomatic_complexity: Optional[int] = Field(default=None, ge=1, le=10_000)
    points: int = Field(default=0, ge=0, le=100_000)


class StaticRuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    required_functions: Optional[list[str]]
    forbidden_imports: Optional[list[str]]
    max_cyclomatic_complexity: Optional[int]
    points: int
