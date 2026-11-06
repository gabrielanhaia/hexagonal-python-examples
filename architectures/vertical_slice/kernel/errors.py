from fastapi import HTTPException


class NotFound(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=404, detail=detail)


class Conflict(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=409, detail=detail)


class Rejected(HTTPException):
    def __init__(self, detail: str) -> None:
        super().__init__(status_code=422, detail=detail)
