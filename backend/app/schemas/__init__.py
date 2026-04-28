from pydantic import BaseModel, Field
from typing import Any


class Response(BaseModel):
    code: int = Field(default=2000)
    message: str = Field(default="success")
    data: Any = Field(default=None)

    @classmethod
    def ok(cls, data: Any = None) -> "Response":
        return cls(code=2000, message="success", data=data)

    @classmethod
    def error(cls, code: int, message: str) -> "Response":
        return cls(code=code, message=message, data=None)


# Error codes
ERROR_TOKEN_EXPIRED = 1001
ERROR_PERMISSION_DENIED = 1002
ERROR_BAD_REQUEST = 2001
ERROR_NOT_FOUND = 2002
ERROR_INTERNAL = 5000
