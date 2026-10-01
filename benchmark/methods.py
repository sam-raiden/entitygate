"""Three extraction/verification methods run over the same cases:

1. naive        -- a plain LLM call, no verification at all. Representative
                    of what most RAG/agent extraction code actually does.
2. faithfulness -- an LLM-as-judge groundedness check: "is this claim
                    supported by the context." Representative of the
                    RAG-faithfulness/entailment-checking category (RAGAS,
                    SelfCheckGPT-style approaches) -- checks truthfulness
                    against the source, never entity ownership.
3. entitygate   -- this repo's own shape + verbatim + entity-anchor gate.

Methods 1 and 2 make real LLM calls (Groq, same provider 7th Sense's own
production pipeline uses) -- a handful of small, cheap calls, not a full
pipeline run.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass

from openai import OpenAI

from entitygate import verify_claim

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_MODEL = "qwen/qwen3.8-27b"

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("GROQ_API_KEY not set -- see .env.example")
        _client = OpenAI(base_url=_GROQ_BASE_URL, api_key=api_key)
    return _client


@dataclass
class MethodResult:
    method: str
    accepted: bool  # did this method accept/return the candidate as correct
    raw: str  # the method's own raw output, for inspection


def naive_llm(case: dict) -> MethodResult:
    """No verification at all -- ask the model to extract the answer from
    the context, trust whatever it says."""
    prompt = (
        f"Using only the text below, answer this question: {case['question']}\n\n"
        f"TEXT:\n{case['source_text']}\n\n"
        f"Respond with STRICT JSON only: {{\"answer\": \"<your answer>\"}}"
    )
    resp = _get_client().chat.completions.create(
        model=_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0, max_tokens=120,
    )
    raw = resp.choices[0].message.content.strip()
    try:
        answer = json.loads(raw.strip("`").removeprefix("json").strip())["answer"]
    except Exception:
        answer = raw
    # "Accepted" means the naive method confidently returned something
    # containing the known candidate string, not an explicit non-answer.
    accepted = case["candidate"].lower() in answer.lower()
    return MethodResult("naive", accepted, answer)


def faithfulness_check(case: dict) -> MethodResult:
    """LLM-as-judge groundedness/entailment check -- the thing RAGAS-style
    faithfulness metrics and NLI-based fabrication detectors do: ask
    whether the claim is SUPPORTED by the context. Deliberately never
    asks about entity ownership -- that's the exact gap this benchmark
    demonstrates."""
    claim = f"{case['entity']}'s answer to \"{case['question']}\" is {case['candidate']}."
    prompt = (
        f"CONTEXT:\n{case['source_text']}\n\n"
        f"CLAIM: {claim}\n\n"
        "Is this claim supported by the context above? Answer strictly "
        'JSON: {"supported": true} or {"supported": false}. Only consider '
        "whether the context contains evidence for the claim's content -- "
        "not whether you independently know it to be true."
    )
    resp = _get_client().chat.completions.create(
        model=_MODEL, messages=[{"role": "user", "content": prompt}], temperature=0, max_tokens=60,
    )
    raw = resp.choices[0].message.content.strip()
    try:
        supported = bool(json.loads(raw.strip("`").removeprefix("json").strip())["supported"])
    except Exception:
        supported = "true" in raw.lower()
    return MethodResult("faithfulness", supported, raw)


def entitygate_check(case: dict) -> MethodResult:
    """This repo's own gate -- no LLM call, deterministic."""
    result = verify_claim(case["candidate"], case["entity"], case["source_text"])
    return MethodResult("entitygate", result.verified, result.reason)
