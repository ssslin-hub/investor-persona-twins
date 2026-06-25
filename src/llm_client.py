"""Thin wrapper around the OpenAI Responses API for the extraction pipeline.

Exposes a single function ``call_llm(prompt, ...)`` that returns the model's
text output. Honors a DRY_RUN environment variable: when set, we don't make a
network call and instead return a stub-JSON or just dump the prompt to disk
for inspection.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5-mini")


def _is_dry_run() -> bool:
    return os.environ.get("DRY_RUN", "").lower() in ("1", "true", "yes")


def call_llm(
    prompt: str,
    *,
    model: str = DEFAULT_MODEL,
    system: str | None = None,
    expect_json: bool = True,
    max_retries: int = 3,
    dry_run_stub: Any = None,
    log_to: str | None = None,
    temperature: float | None = None,
    seed: int | None = None,
    return_response: bool = False,
) -> Any:
    """Call the OpenAI Chat Completions API and return the assistant text.

    If DRY_RUN is set in the environment, return ``json.dumps(dry_run_stub)``
    instead so the rest of the pipeline can be exercised without spending
    tokens.
    """
    if log_to:
        os.makedirs(os.path.dirname(log_to), exist_ok=True)
        with open(log_to, "w") as fp:
            fp.write(prompt)

    if _is_dry_run():
        if dry_run_stub is None:
            dry_run_stub = {"_dry_run": True, "prompt_len": len(prompt)}
        return json.dumps(dry_run_stub)

    from openai import OpenAI  # imported lazily so dry-run doesn't need it
    client = OpenAI()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_err: Exception | None = None
    for attempt in range(max_retries):
        try:
            kwargs: dict[str, Any] = {"model": model, "messages": messages}
            if expect_json:
                kwargs["response_format"] = {"type": "json_object"}
            if temperature is not None:
                kwargs["temperature"] = temperature
            if seed is not None:
                kwargs["seed"] = seed
            try:
                resp = client.chat.completions.create(**kwargs)
            except Exception as e:
                # Some reasoning models reject temperature/seed; retry without.
                err_lc = str(e).lower()
                retried = False
                if temperature is not None and "temperature" in err_lc:
                    kwargs.pop("temperature", None)
                    retried = True
                if seed is not None and "seed" in err_lc:
                    kwargs.pop("seed", None)
                    retried = True
                if retried:
                    resp = client.chat.completions.create(**kwargs)
                else:
                    raise
            content = resp.choices[0].message.content or ""
            if return_response:
                return content, resp
            return content
        except Exception as e:  # noqa: BLE001
            last_err = e
            time.sleep(2 ** attempt)
    raise RuntimeError(f"LLM call failed after {max_retries} retries: {last_err}")


def parse_json_strict(text: str) -> Any:
    """Parse a JSON object out of an LLM response. Tolerates leading/trailing
    prose by extracting the first balanced ``{ ... }`` block.
    """
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Find first '{' and try to match the balanced closing brace.
        start = text.find("{")
        if start == -1:
            raise
        depth = 0
        for i in range(start, len(text)):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start : i + 1])
        raise
