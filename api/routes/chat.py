"""
Natural language Copilot/chat endpoint grounded in mathematical execution evidence.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional

from orchestration.intent_parser import IntentParser
from orchestration.router import ModelRouter
from orchestration.evidence_envelope import GroundedEvidenceEnvelope
from connectors import MockDataProvider

from api.routes.connectors import _providers

router = APIRouter(prefix="/api/chat", tags=["Copilot"])


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    user_query: str
    intent: Dict[str, Any]
    envelope: GroundedEvidenceEnvelope
    reply: str


@router.post("", response_model=ChatResponse)
def handle_chat(req: ChatRequest):
    # Select Databricks if connected, otherwise mock lakehouse
    provider = _providers.get("databricks_primary")
    if not provider or not provider.test_connection():
        provider = _providers.get("mock_lakehouse")

    active_router = ModelRouter(data_provider=provider)
    intent = IntentParser.parse(req.message)
    envelope = active_router.route_and_execute(intent)

    return ChatResponse(
        user_query=req.message,
        intent=intent.model_dump(),
        envelope=envelope,
        reply=envelope.grounded_summary,
    )
