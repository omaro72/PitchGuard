from typing import Self

from pydantic import ConfigDict, Field, model_validator

from app.schemas import PitchGuardSchema


class DecisionPolicy(PitchGuardSchema):
    model_config = ConfigDict(extra="forbid", frozen=True)

    block_relevance_below: int = Field(default=40, ge=0, le=100)
    pass_relevance_at_least: int = Field(default=70, ge=0, le=100)
    minimum_personalization: int = Field(default=60, ge=0, le=100)

    @model_validator(mode="after")
    def validate_relevance_range(self) -> Self:
        if self.block_relevance_below >= self.pass_relevance_at_least:
            raise ValueError("block_relevance_below must be lower than pass_relevance_at_least")
        return self
