"""Explicit paid-provider mode, independent of trace export."""

import os

from _shared import run_case


def action(provider):
    from ibm_watsonx_ai import APIClient, Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference

    key = os.environ["WATSONX_API_KEY"]
    project = os.environ["WATSONX_PROJECT_ID"]
    model = os.environ["WATSONX_MODEL_ID"]
    client = APIClient(
        Credentials(
            url=os.environ.get("WATSONX_URL", "https://us-south.ml.cloud.ibm.com"),
            api_key=key,
        ),
        project_id=project,
    )
    try:
        native = ModelInference(
            api_client=client, model_id=model, validate=False, max_retries=0
        )
        result = native.generate_text(
            prompt="Reply with a short greeting.", params={"max_new_tokens": 16}
        )
        assert type(result) is str
        return "live generation completed"
    finally:
        client.httpx_client.close()


if __name__ == "__main__":
    if os.getenv("RESPAN_WATSONX_LIVE") != "1":
        print(
            "SKIP: set RESPAN_WATSONX_LIVE=1 with explicit provider credentials/model/project."
        )
    else:
        run_case("watsonx_optional_live", action)
