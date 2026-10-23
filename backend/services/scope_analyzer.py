"""Topic Scope Analyzer Service using NVIDIA LLM and Pydantic validation.
Decomposes raw research topics into PICO-CS frameworks, generates 3 RQs,
search queries, and feasibility scores.
"""

import json
import logging
from typing import Optional
from backend.core.nvidia_client import nvidia_client
from backend.schemas.contracts import ScopeAnalysisRequest, ScopeAnalysisResult, BooleanQueries

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert scientific research director and AI research methodology specialist.
Analyze the given raw research topic and decompose it using the PICO-CS framework:
- Problem: Population or core technical challenge being addressed.
- Method: Intervention, model architecture, or primary technical mechanism.
- Comparison: Baseline models, standard benchmark procedures, or traditional counter-approaches.
- Outcomes: Target metrics, evaluation criteria, and expected scientific contributions.

You MUST generate:
1. Exactly THREE (3) distinct, rigorous, and highly actionable research questions (RQ1, RQ2, RQ3).
2. Boolean search queries tailored for OpenAlex, arXiv, and GitHub repositories.
3. A Feasibility Score between 0 and 100 based on technical difficulty, data availability, and 7-day feasibility.
4. An informative verdict string (e.g. "Feasible and Well-Scoped for 7-Day Sprint", "Scope Too Broad: Requires Domain Narrowing").
5. Critical warnings if the topic suffers from known pitfalls (e.g., temporal data leakage, unrealistic computation requirements).

You MUST respond strictly with valid JSON conforming to this schema:
{
  "original_topic": "string",
  "problem": "string",
  "method": "string",
  "comparison": "string",
  "outcomes": "string",
  "research_questions": [
    "RQ1: ...",
    "RQ2: ...",
    "RQ3: ..."
  ],
  "boolean_queries": {
    "openalex": "string",
    "arxiv": "string",
    "github": "string"
  },
  "feasibility_score": 85,
  "verdict": "string",
  "warnings": ["string", "string"]
}
"""


async def analyze_topic_scope(request: ScopeAnalysisRequest) -> ScopeAnalysisResult:
    """Analyze a research topic and return a validated ScopeAnalysisResult."""
    user_prompt = f"Research Topic: {request.topic}\n"
    if request.constraints:
        user_prompt += f"Constraints & Boundaries: {request.constraints}\n"

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt}
    ]

    raw_response, is_mock = await nvidia_client.generate_chat(messages=messages, temperature=0.1)

    try:
        parsed_json = json.loads(raw_response)
        parsed_json["original_topic"] = request.topic
        parsed_json["is_mock"] = is_mock
        result = ScopeAnalysisResult.model_validate(parsed_json)
        return result
    except Exception as err:
        logger.warning(f"Failed to validate LLM output ({err}). Repairing with safe fallback structure.")
        # Ensure contract guarantees are never broken even if model returned non-conforming JSON
        return ScopeAnalysisResult(
            original_topic=request.topic,
            problem=f"Technical challenges and distribution shift in {request.topic}.",
            method="Comparative evaluation across benchmarks and robust architectural adaptation.",
            comparison="State-of-the-art baselines and traditional machine learning pipelines.",
            outcomes="Empirical generalization bounds, cross-dataset transfer metrics, and robustness verification.",
            research_questions=[
                f"RQ1: What is the extent of performance degradation observed when applying models in {request.topic} across heterogeneous environments?",
                f"RQ2: Which architectural or data-centric defenses best mitigate feature decay and concept drift in {request.topic}?",
                f"RQ3: How do adversarial perturbations affect classifier boundaries compared to nominal data distributions?"
            ],
            boolean_queries=BooleanQueries(
                openalex=f'("{request.topic}") AND ("machine learning" OR "deep learning") AND ("robustness" OR "evaluation")',
                arxiv=f'all:"{request.topic}" AND (all:"benchmark" OR all:"generalization")',
                github=f'"{request.topic}" AND ("benchmark" OR "dataset")'
            ),
            feasibility_score=85,
            verdict="Feasible and Well-Scoped for 7-Day Sprint",
            warnings=[
                "Schema recovery applied: Ensure structured JSON output constraint is enforced by the provider.",
                "Verify cross-dataset splits using chronological ordering."
            ],
            is_mock=True
        )
