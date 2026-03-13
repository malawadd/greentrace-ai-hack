"""
PydanticAI Orchestrator – ESG Investigation Agent
===================================================
Connects:  Qdrant retrieval → PydanticAI agent → LLM analysis → structured ESG output.

Env vars required:
    GROQ_API_KEY   – Groq API key
    GROQ_MODEL     – (optional) defaults to llama-3.3-70b-versatile
"""

from __future__ import annotations

import json
import os
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider

from app.schemas.retrieval import RetrievalRequest, RetrievalResponse


# ---------------------------------------------------------------------------
# Structured output schema
# ---------------------------------------------------------------------------

class ESGAnalysisResult(BaseModel):
    """Structured output the LLM must produce."""

    claim: str = Field(
        description="The sustainability / ESG claim being investigated."
    )
    supporting_evidence: list[str] = Field(
        default_factory=list,
        description="List of evidence points that SUPPORT the claim, drawn only from retrieved sources.",
    )
    contradicting_evidence: list[str] = Field(
        default_factory=list,
        description="List of evidence points that CONTRADICT or cast doubt on the claim, drawn only from retrieved sources.",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="URLs of the sources referenced in the analysis.",
    )
    verdict: str = Field(
        description=(
            "A concise overall verdict on the claim's accuracy "
            "(e.g. 'Largely Supported', 'Partially Misleading', 'Greenwashing Risk')."
        ),
    )


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are GreenTrace AI, an expert ESG (Environmental, Social, Governance) investigator.

Your job:
1. Analyze the user's sustainability-related question about a company.
2. Use ONLY the retrieved source documents provided in the context below to form your analysis.
3. Identify evidence that SUPPORTS the company's claim and evidence that CONTRADICTS it.
4. NEVER invent, fabricate, or hallucinate sources or evidence. If the retrieved context is insufficient, say so explicitly.
5. Cite source URLs whenever you reference a piece of evidence.
6. Provide a clear, concise verdict on whether the claim is accurate, misleading, or unsubstantiated.

Always respond with the structured output format requested.
"""


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class PydanticAIOrchestrator:
    """Real PydanticAI orchestrator that calls an LLM via Groq."""

    def __init__(self) -> None:
        self._api_key: str = os.getenv("GROQ_API_KEY", "")
        self._model_name: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        self._agent: Agent[None, ESGAnalysisResult] | None = None  # type: ignore[type-arg]

        if self._api_key:
            model = GroqModel(
                self._model_name,
                provider=GroqProvider(api_key=self._api_key),
            )
            self._agent = Agent(
                model,
                output_type=ESGAnalysisResult,
                system_prompt=_SYSTEM_PROMPT,
            )

    # ------------------------------------------------------------------
    # Context builder
    # ------------------------------------------------------------------

    @staticmethod
    def _build_context(retrieval: RetrievalResponse) -> str:
        """Build a numbered context block from retrieved evidence hits."""
        if not retrieval.evidence:
            return "(No relevant sources were retrieved.)"

        parts: list[str] = []
        for idx, hit in enumerate(retrieval.evidence, start=1):
            title = hit.title or "(no title)"
            snippet = hit.text or "(no snippet)"
            url = hit.url or "(no url)"
            parts.append(
                f"Source {idx}:\n"
                f"Title: {title}\n"
                f"Snippet: {snippet}\n"
                f"URL: {url}"
            )
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def orchestrate(
        self,
        request: RetrievalRequest,
        retrieval: RetrievalResponse,
    ) -> dict[str, str]:
        """
        Run the full orchestration pipeline:
            context building → PydanticAI agent → structured output → dict

        Returns dict[str, str] to stay compatible with MockAnswerResponse.orchestration.
        """

        # Fallback if LLM is not configured
        if self._agent is None:
            return {
                "agent": "pydanticai (LLM not configured)",
                "company": request.company,
                "question": request.question,
                "evidence_count": str(retrieval.total_hits),
                "error": "GROQ_API_KEY is not set. Set it in .env to enable LLM analysis.",
            }

        # Build context from retrieved evidence
        context = self._build_context(retrieval)

        # Compose the user prompt
        user_prompt = (
            f"Company: {request.company}\n"
            f"Question: {request.question}\n\n"
            f"--- Retrieved Evidence ---\n{context}\n"
            f"--- End of Evidence ---\n\n"
            f"Analyze the above evidence and provide your structured ESG investigation."
        )

        # Run the PydanticAI agent synchronously
        result = self._agent.run_sync(user_prompt)
        analysis: ESGAnalysisResult = result.output

        # Convert structured result to dict[str, str] for backward compatibility
        return {
            "agent": "pydanticai",
            "company": request.company,
            "question": request.question,
            "evidence_count": str(retrieval.total_hits),
            "claim": analysis.claim,
            "supporting_evidence": json.dumps(analysis.supporting_evidence),
            "contradicting_evidence": json.dumps(analysis.contradicting_evidence),
            "sources": json.dumps(analysis.sources),
            "verdict": analysis.verdict,
        }


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def get_pydanticai_orchestrator() -> PydanticAIOrchestrator:
    return PydanticAIOrchestrator()
