class RewriteFlowError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class AuthenticationError(RewriteFlowError):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class BadRequestError(RewriteFlowError):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class ConflictError(RewriteFlowError):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class NotFoundError(RewriteFlowError):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
