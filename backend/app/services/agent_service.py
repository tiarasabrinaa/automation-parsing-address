import ollama

from app.core.config import settings
from app.schemas.agent import AgentRequest, AgentResponse


client = ollama.Client(host=settings.ollama_base_url)


class AgentService:
    def execute(self, request: AgentRequest) -> AgentResponse:

        try:
            response = client.chat(
                model=settings.ollama_model,
                messages=[{"role": "user", "content": request.prompt}],
            )
            return AgentResponse(
                success=True,
                message="Agent request processed successfully.",
                result=response["message"]["content"],
            )
        except Exception as e:
            return AgentResponse(
                success=False,
                message=f"Error processing agent request: {str(e)}",
                result=None,
            )