from __future__ import annotations

from app.schemas.retrieval import MockAnswerResponse, RetrievalRequest
from app.services.llm_answer_service import get_llm_answer_service
from app.services.pydanticai_orchestrator import get_pydanticai_orchestrator
from app.services.retrieval_service import get_retrieval_service


class MockAnswerService:
    def __init__(self) -> None:
        self.retrieval = get_retrieval_service()
        self.orchestrator = get_pydanticai_orchestrator()
        self.answerer = get_llm_answer_service()

    def answer(self, request: RetrievalRequest) -> MockAnswerResponse:
        retrieval = self.retrieval.retrieve(request)
        orchestration = self.orchestrator.orchestrate(request, retrieval)

        # Use real LLM verdict when available, fall back to mock
        if orchestration.get("verdict"):
            answer_status = "grounded"
            answer = (
                f"Verdict: {orchestration['verdict']}. "
                f"Claim: {orchestration.get('claim', request.question)}. "
                f"Supporting evidence: {orchestration.get('supporting_evidence', 'N/A')}. "
                f"Contradicting evidence: {orchestration.get('contradicting_evidence', 'N/A')}."
            )
        else:
            answer_status = "mocked"
            answer = self.answerer.generate(request, retrieval)

        return MockAnswerResponse(
            company=request.company,
            question=request.question,
            answer_status=answer_status,
            answer=answer,
            retrieval=retrieval,
            orchestration=orchestration,
        )


def get_mock_answer_service() -> MockAnswerService:
    return MockAnswerService()
