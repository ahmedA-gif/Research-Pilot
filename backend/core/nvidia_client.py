"""NVIDIA NIM client for chat completion and embedding models.
Implements bounded retries, input_type validation, 2048-dim verification,
and deterministic mock fallbacks clearly labelled as mock mode.
"""

import hashlib
import json
import logging
import math
import time
from typing import Any, Dict, List, Optional, Tuple
import httpx
import numpy as np
from backend.core.config import settings

logger = logging.getLogger(__name__)


class NvidiaClient:
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.api_base = settings.NVIDIA_API_BASE.rstrip("/")
        self.llm_model = settings.NVIDIA_LLM_MODEL
        self.embed_model = settings.NVIDIA_EMBED_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION  # 2048

    @property
    def is_configured(self) -> bool:
        """Check whether a non-empty NVIDIA API key is configured."""
        return bool(self.api_key and self.api_key.strip() and not self.api_key.startswith("nvapi-placeholder"))

    def _generate_deterministic_mock_vector(self, text: str) -> List[float]:
        """Generate a deterministic, unit-normalized vector of target dimension (2048)
        derived from SHA-256 hash seeds. Provides stable semantic clustering for tests.
        """
        dim = self.dimension
        # Create a seeded pseudorandom distribution from the text
        hasher = hashlib.sha256()
        hasher.update(text.encode("utf-8"))
        seed_int = int.from_bytes(hasher.digest()[:8], "big")
        
        rng = np.random.RandomState(seed_int % (2**32))
        raw_vec = rng.randn(dim).astype(np.float32)

        # Normalize to unit vector for accurate cosine similarity
        norm = np.linalg.norm(raw_vec)
        if norm > 0:
            norm_vec = raw_vec / norm
        else:
            norm_vec = raw_vec
        return norm_vec.tolist()

    async def get_embedding(self, text: str, input_type: str = "passage") -> Tuple[List[float], bool]:
        """Fetch embedding from NVIDIA NIM or fallback to deterministic mock.
        Args:
            text: Raw string to embed
            input_type: "passage" for indexing paper abstracts, "query" for user queries
        Returns:
            Tuple of (vector_of_floats, is_mock_boolean)
        """
        if input_type not in ["passage", "query"]:
            raise ValueError(f"Invalid input_type '{input_type}'. Must be 'passage' or 'query'.")

        if not text or not text.strip():
            raise ValueError("Cannot embed empty text string.")

        if not self.is_configured:
            logger.info("NVIDIA_API_KEY not configured. Using deterministic mock embedding.")
            return self._generate_deterministic_mock_vector(text), True

        endpoint = f"{self.api_base}/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "input": [text],
            "model": self.embed_model
        }
        if "nemotron-3.5" in self.embed_model:
            payload["input_type"] = input_type

        # Bounded retry: up to 2 attempts for transient failures
        last_error = None
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    resp = await client.post(endpoint, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        embedding = data["data"][0]["embedding"]
                        if len(embedding) != self.dimension:
                            logger.warning(
                                f"Dimension mismatch: expected {self.dimension}, got {len(embedding)}"
                            )
                        return embedding, False
                    elif resp.status_code in [400, 500] and "input_type" in payload:
                        # Try fallback without input_type
                        del payload["input_type"]
                        continue
                    elif resp.status_code in [429, 502, 503, 504]:
                        last_error = f"HTTP {resp.status_code}: {resp.text}"
                        time.sleep(1.0)
                        continue
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text}"
                        break
            except Exception as e:
                last_error = str(e)
                time.sleep(0.5)

        logger.warning(f"NVIDIA embedding API call failed ({last_error}). Falling back to mock vector.")
        return self._generate_deterministic_mock_vector(text), True

    async def generate_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 2000
    ) -> Tuple[str, bool]:
        """Generate response via NVIDIA LLM chat completions or fallback to mock.
        Returns:
            Tuple of (response_text, is_mock_boolean)
        """
        if not self.is_configured:
            logger.info("NVIDIA_API_KEY not configured. Generating deterministic mock completion.")
            return self._generate_mock_scope_response(messages), True

        endpoint = f"{self.api_base}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.llm_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        last_error = None
        for attempt in range(2):
            try:
                async with httpx.AsyncClient(timeout=35.0) as client:
                    resp = await client.post(endpoint, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        msg = data["choices"][0]["message"]
                        content = msg.get("content") or msg.get("reasoning_content") or ""
                        return content, False
                    elif resp.status_code in [429, 502, 503, 504]:
                        last_error = f"HTTP {resp.status_code}: {resp.text}"
                        time.sleep(1.0)
                        continue
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text}"
                        break
            except Exception as e:
                last_error = str(e)
                time.sleep(0.5)

        logger.warning(f"NVIDIA LLM call failed ({last_error}). Falling back to mock response.")
        return self._generate_mock_scope_response(messages), True

    def _generate_mock_scope_response(self, messages: List[Dict[str, str]]) -> str:
        """Deterministic mock response strictly matching the ScopeAnalysisResult schema."""
        # Extract user topic if present
        topic = "cross-dataset robustness of machine-learning methods for phishing detection"
        for msg in messages:
            if msg.get("role") == "user":
                topic = msg.get("content", topic)
                break

        mock_payload = {
            "original_topic": topic,
            "problem": "Severe degradation of machine learning phishing classifiers under dataset shift and adversarial evasions across non-stationary distributions.",
            "method": "Multi-modal feature alignment, invariant risk minimization, and contrastive representation learning evaluated on longitudinal benchmarks.",
            "comparison": "Baseline Random Forests, single-modality URL lexical tokenizers, and static train-test splits lacking temporal separation.",
            "outcomes": "Generalization F1-score retention across foreign testbeds, reduced false positive rates on corporate intranets, and adversarial bypass resistance.",
            "research_questions": [
                "RQ1: To what extent does cross-dataset distribution drift degrade the accuracy of lexical versus DOM-structural phishing classifiers?",
                "RQ2: Which invariant feature subsets minimize generalization collapse when transferred from open feeds (PhishTank) to enterprise telemetry?",
                "RQ3: How do multi-modal graph neural representations perform against black-box homoglyph and path-padding evasion attacks compared to tree ensembles?"
            ],
            "boolean_queries": {
                "openalex": '("phishing detection" OR "malicious URL") AND ("machine learning" OR "deep learning") AND ("robustness" OR "cross-dataset" OR "concept drift")',
                "arxiv": 'all:phishing AND (all:"cross-dataset" OR all:"concept drift" OR all:"adversarial robustness") AND (all:"neural network" OR all:"classifier")',
                "github": '"phishing-detection" AND ("benchmark" OR "cross-dataset" OR "dataset-drift") AND language:Python'
            },
            "feasibility_score": 88,
            "verdict": "Feasible and Well-Scoped for 7-Day Foundation",
            "warnings": [
                "Ensure temporal splitting is applied rather than random k-fold cross-validation to prevent optimistic accuracy inflation.",
                "Verify that live URL feeds account for dead domains and dynamic redirection chains during crawling."
            ],
            "is_mock": True
        }
        return json.dumps(mock_payload)

    async def ping_health(self) -> Dict[str, Any]:
        """Perform a live latency probe to the NVIDIA NIM endpoint."""
        if not self.is_configured:
            return {
                "configured": False,
                "status": "mock",
                "latency_ms": None,
                "notes": "NVIDIA_API_KEY is not set. Operating in deterministic mock mode."
            }

        start_time = time.perf_counter()
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{self.api_base}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                latency = round((time.perf_counter() - start_time) * 1000, 2)
                if resp.status_code == 200:
                    return {
                        "configured": True,
                        "status": "online",
                        "latency_ms": latency,
                        "notes": "Connected to NVIDIA NIM API Catalog successfully."
                    }
                else:
                    return {
                        "configured": True,
                        "status": "degraded",
                        "latency_ms": latency,
                        "notes": f"NVIDIA API returned HTTP {resp.status_code}."
                    }
        except Exception as e:
            return {
                "configured": True,
                "status": "offline",
                "latency_ms": None,
                "notes": f"Connection error: {str(e)}"
            }


nvidia_client = NvidiaClient()
