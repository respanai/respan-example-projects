"""Synthetic provider failure; catches the original SDK exception."""

import os

from _shared import make_client, run_example
from groq import InternalServerError


def scenario():
    if os.getenv("RESPAN_GROQ_FIXTURE") != "1":
        raise RuntimeError(
            "This controlled-error example requires RESPAN_GROQ_FIXTURE=1"
        )
    with make_client() as client:
        try:
            client.chat.completions.create(
                model="fixture-error",
                messages=[{"role": "user", "content": "Synthetic failure"}],
            )
        except InternalServerError as exc:
            assert exc.status_code == 503
            return {"caught_status": exc.status_code}
    raise AssertionError("Expected the controlled 503")


if __name__ == "__main__":
    run_example("controlled-error", scenario)
