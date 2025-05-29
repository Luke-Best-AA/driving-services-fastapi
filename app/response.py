from pydantic import BaseModel
from typing import Any, Optional

class APIResponse(BaseModel):
    status: int
    message: Optional[str] = None  # Optional message for additional context
    data: Optional[Any] = None  # Flexible field for any additional data