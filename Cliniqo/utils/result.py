from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Result:
    """
    Returned by every service method.
    Never raise exceptions to the UI — always return a Result.
    """
    success: bool
    message: str
    data: Optional[Any] = None

    @staticmethod
    def ok(data=None, message="Success"):
        return Result(success=True, message=message, data=data)

    @staticmethod
    def fail(message="Something went wrong", data=None):
        return Result(success=False, message=message, data=data)
