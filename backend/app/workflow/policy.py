from pydantic import ConfigDict, Field

from app.schemas import PitchGuardSchema


class ReviewWorkflowPolicy(PitchGuardSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)

    max_attempts: int = Field(default=2, ge=1, le=3)
    retry_delay_seconds: float = Field(default=0.25, ge=0, le=5)
    attempt_timeout_seconds: float = Field(default=130, ge=1, le=600)
