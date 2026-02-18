from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class IOTestCaseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    stdin: Optional[str] = None
    expected_stdout: str = Field(min_length=1)
    points: int = Field(default=1, ge=0, le=100000)
    is_hidden: bool = True
    order_index: int = Field(default=0, ge=0)

class IOTestCaseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    assignment_id: int
    name: str
    stdin: Optional[str]
    expected_stdout: str
    points: int
    is_hidden: bool
    order_index: int
