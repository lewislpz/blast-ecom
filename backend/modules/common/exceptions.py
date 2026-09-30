from rest_framework.exceptions import APIException


class DomainOperationError(APIException):
    """Translate a stable domain result into the shared Problem Details contract."""

    def __init__(self, *, status_code: int, code: str) -> None:
        self.status_code = status_code
        super().__init__(detail="The operation could not be completed.", code=code)
