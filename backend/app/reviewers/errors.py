from app.schemas import ReviewerName


class ReviewerContractError(Exception):
    def __init__(
        self,
        *,
        reviewer: ReviewerName,
        code: str,
        message: str,
        retryable: bool = True,
    ) -> None:
        super().__init__(message)
        self.reviewer = reviewer
        self.code = code
        self.message = message
        self.retryable = retryable
