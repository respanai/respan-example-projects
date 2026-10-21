"""Optional paid provider call; separate from controlled native fixtures."""

import os

from _shared import run_example

if __name__ == "__main__":
    if os.getenv("RESPAN_EXAMPLE_LIVE") == "1":
        run_example("live_provider")
    else:
        print(
            "SKIP live_provider: set RESPAN_EXAMPLE_LIVE=1, ANTHROPIC_API_KEY and ANTHROPIC_MODEL to opt in"
        )
