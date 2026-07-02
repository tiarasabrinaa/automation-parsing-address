from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    prompt: str = Field(..., description="User prompt or task instruction")
    context: str | None = Field(default=None, description="Optional supporting context")


class AgentResponse(BaseModel):
    success: bool
    message: str
    result: str | None = None
