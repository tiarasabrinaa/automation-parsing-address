from fastapi import APIRouter

from app.schemas.agent import AgentRequest, AgentResponse
from app.services.agent_service import AgentService

router = APIRouter()
service = AgentService()

@router.post("/agent/execute", response_model=AgentResponse)
def execute_agent(request: AgentRequest) -> AgentResponse:
    return service.execute(request)