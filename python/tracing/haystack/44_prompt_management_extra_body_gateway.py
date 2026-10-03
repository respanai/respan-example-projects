"""Create and use a Respan managed prompt from Haystack via ``extra_body``.

Haystack's ``OpenAIChatGenerator`` accepts OpenAI SDK keyword arguments through
``generation_kwargs``. This example first creates and deploys a prompt on the
Respan platform using ``RESPAN_API_KEY``. The Haystack run then passes only the
managed ``prompt_id`` and variables under ``generation_kwargs.extra_body.prompt``
so the Respan gateway resolves the deployed prompt at request time.

This example uses the Respan gateway for the LLM call too. ``configure_respan``
sets ``OPENAI_API_KEY`` to ``RESPAN_API_KEY`` and points ``OPENAI_BASE_URL`` at
the Respan OpenAI-compatible gateway, so no OpenAI provider key is required when
the Respan key has credits or managed gateway access.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from _shared import configure_respan, finish_respan, print_result
from dotenv import find_dotenv, load_dotenv


def _prompt_variables() -> dict[str, Any]:
    variables_json = os.getenv("RESPAN_PROMPT_VARIABLES_JSON")
    if variables_json:
        try:
            variables = json.loads(variables_json)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "RESPAN_PROMPT_VARIABLES_JSON must be valid JSON."
            ) from exc
        if not isinstance(variables, dict):
            raise RuntimeError("RESPAN_PROMPT_VARIABLES_JSON must decode to an object.")
        return variables

    return {
        "question": os.getenv("RESPAN_PROMPT_QUESTION", "Who created Python?"),
        "context": os.getenv(
            "RESPAN_PROMPT_CONTEXT",
            "Python was created by Guido van Rossum and first released in 1991.",
        ),
    }


def _schema_version() -> int:
    value = os.getenv("RESPAN_PROMPT_SCHEMA_VERSION", "2")
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError("RESPAN_PROMPT_SCHEMA_VERSION must be an integer.") from exc


def _management_timeout_seconds() -> float:
    value = os.getenv("RESPAN_MANAGEMENT_TIMEOUT_SECONDS", "30")
    try:
        return float(value)
    except ValueError as exc:
        raise RuntimeError(
            "RESPAN_MANAGEMENT_TIMEOUT_SECONDS must be a number."
        ) from exc


def _respan_api_key() -> str:
    api_key = os.getenv("RESPAN_API_KEY")
    if not api_key:
        raise RuntimeError("RESPAN_API_KEY is required to create managed prompts.")
    return api_key


def _respan_base_url() -> str:
    return os.getenv("RESPAN_BASE_URL", "https://api.respan.ai/api").rstrip("/")


def _request_respan_json(
    method: str,
    path: str,
    *,
    api_key: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    url = f"{_respan_base_url()}{path}"
    body = None
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    request = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(request, timeout=_management_timeout_seconds()) as response:
            response_body = response.read().decode("utf-8")
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Respan API {method} {path} failed with HTTP {exc.code}: {error_body}"
        ) from exc
    except URLError as exc:
        raise RuntimeError(f"Respan API {method} {path} failed: {exc}") from exc

    if not response_body:
        return {}
    data = json.loads(response_body)
    if not isinstance(data, dict):
        raise TypeError(f"Respan API {method} {path} returned a non-object JSON body.")
    return data


def _response_id(data: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = data.get(key)
        if value:
            return str(value)
    raise RuntimeError(f"Respan API response is missing one of: {', '.join(keys)}")


def _version_number(data: dict[str, Any]) -> int:
    value = data.get("version")
    if value is None:
        value = data.get("version_number")
    if value is None:
        raise RuntimeError("Respan prompt version response is missing version.")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise RuntimeError(f"Invalid Respan prompt version value: {value!r}") from exc


def _managed_prompt_name() -> str:
    configured_name = os.getenv("RESPAN_MANAGED_PROMPT_NAME")
    if configured_name:
        return configured_name
    created_at = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"Haystack extra_body gateway prompt {created_at}"


def _default_system_message(prompt_variables: dict[str, Any]) -> str:
    if {"question", "context"}.issubset(prompt_variables):
        return (
            "Answer the user's question using only the provided context. "
            "If the answer is not in the context, say you do not know."
        )
    return "Respond to the user request clearly and concisely."


def _default_user_template(prompt_variables: dict[str, Any]) -> str:
    if {"question", "context"}.issubset(prompt_variables):
        return "Question: {{question}}\n\nContext:\n{{context}}"

    for key in ("customer_inquiry", "user_query", "question"):
        if key in prompt_variables:
            return f"{{{{{key}}}}}"

    if prompt_variables:
        return "\n".join(f"{key}: {{{{{key}}}}}" for key in sorted(prompt_variables))
    return "Run the managed prompt."


def _managed_prompt_messages(prompt_variables: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "role": "system",
            "content": os.getenv(
                "RESPAN_MANAGED_PROMPT_SYSTEM_MESSAGE",
                _default_system_message(prompt_variables),
            ),
        },
        {
            "role": "user",
            "content": os.getenv(
                "RESPAN_MANAGED_PROMPT_USER_TEMPLATE",
                _default_user_template(prompt_variables),
            ),
        },
    ]


def _managed_prompt_max_tokens() -> int:
    value = os.getenv("RESPAN_MANAGED_PROMPT_MAX_TOKENS", "256")
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(
            "RESPAN_MANAGED_PROMPT_MAX_TOKENS must be an integer."
        ) from exc


def _create_and_deploy_managed_prompt(
    prompt_variables: dict[str, Any],
) -> tuple[str, int]:
    api_key = _respan_api_key()
    messages = _managed_prompt_messages(prompt_variables)
    model = os.getenv("RESPAN_MODEL", "gpt-4o")
    version_payload = {
        "description": "Prompt created by the Haystack extra_body gateway example.",
        "messages": messages,
        "model": model,
        "stream": False,
        "temperature": 0.0,
        "max_tokens": _managed_prompt_max_tokens(),
        "variables": prompt_variables,
        "readonly": True,
    }

    prompt = _request_respan_json(
        "POST",
        "/prompts/",
        api_key=api_key,
        payload={
            "name": _managed_prompt_name(),
            "description": (
                "Created by the Haystack extra_body gateway example. The runtime "
                "call passes only this prompt_id and variables."
            ),
        },
    )
    prompt_id = _response_id(prompt, "prompt_id", "id", "full_prompt_id")

    created_version = _request_respan_json(
        "POST",
        f"/prompts/{prompt_id}/versions/",
        api_key=api_key,
        payload=version_payload,
    )
    version = _version_number(created_version)

    # A second draft commits the first version so it can be deployed.
    commit_payload = {
        **version_payload,
        "description": "Draft created to commit the deployed example version.",
    }
    _request_respan_json(
        "POST",
        f"/prompts/{prompt_id}/versions/",
        api_key=api_key,
        payload=commit_payload,
    )

    _request_respan_json(
        "PATCH",
        f"/prompts/{prompt_id}/versions/{version}/",
        api_key=api_key,
        payload={"deploy": True},
    )

    print(f"Created and deployed Respan prompt {prompt_id} version {version}.")
    return prompt_id, version


def _haystack_required_message(prompt_variables: dict[str, Any]) -> str:
    for key in ("customer_inquiry", "question", "user_query"):
        value = prompt_variables.get(key)
        if isinstance(value, str) and value:
            return value
    return "Run the managed Respan prompt."


def run_prompt_management_extra_body_gateway_example() -> dict[str, Any]:
    load_dotenv(find_dotenv(), override=False)

    prompt_variables = _prompt_variables()
    prompt_id, deployed_version = _create_and_deploy_managed_prompt(prompt_variables)
    prompt_config = {
        "prompt_id": prompt_id,
        "schema_version": _schema_version(),
        "variables": prompt_variables,
        "override": True,
    }

    respan = configure_respan(
        "haystack-prompt-management-extra-body-gateway",
        use_gateway=True,
    )
    try:
        from haystack import Pipeline
        from haystack.components.generators.chat import OpenAIChatGenerator
        from haystack.dataclasses import ChatMessage

        pipeline = Pipeline()
        pipeline.add_component(
            "managed_prompt_llm",
            OpenAIChatGenerator(model=os.getenv("RESPAN_MODEL", "gpt-4o")),
        )

        with respan.propagate_attributes(prompt=prompt_config):
            result = pipeline.run(
                {
                    "managed_prompt_llm": {
                        # Haystack requires at least one message to call the
                        # OpenAI-compatible generator. The Respan gateway reads
                        # extra_body.prompt and overrides this placeholder.
                        "messages": [
                            ChatMessage.from_user(
                                _haystack_required_message(prompt_variables)
                            )
                        ],
                        "generation_kwargs": {
                            "temperature": 0.0,
                            "extra_body": {
                                # Only the managed prompt id and variables are
                                # sent with the LLM call. The prompt messages
                                # were stored on the Respan platform above.
                                "prompt": prompt_config,
                            },
                        },
                    }
                }
            )

        output = {
            "managed_prompt_id": prompt_id,
            "managed_prompt_version": deployed_version,
            "haystack_result": result,
        }
        print_result("Respan prompt management via extra_body", output)
        return output
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    run_prompt_management_extra_body_gateway_example()
