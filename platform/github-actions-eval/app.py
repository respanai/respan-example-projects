"""Acme support bot: the code under test.

`answer()` is what ships to production. The CI eval (respan_eval.py)
runs it over a Respan dataset of golden questions and scores the answers.
"""

import os

from openai import OpenAI

MODEL = "gpt-4o-mini"

SYSTEM_PROMPT = """You are Acme's customer-support assistant. Answer in one or two sentences,
using only these policies:
- Returns: within 30 days of delivery, full refund.
- Shipping: free on orders over $50, otherwise a flat $5.99.
- Human support: Monday to Friday, 9am to 5pm Pacific time.
- Password reset: Settings > Security > Reset password; a reset link is emailed.
- Warranty: Acme blenders have a 2-year limited warranty.
If a question is not covered, say you will connect the customer to a human."""

# Any OpenAI-compatible client works: point it at the Respan gateway.
client = OpenAI(
    base_url=f"{os.environ['RESPAN_BASE_URL']}/api",
    api_key=os.environ["RESPAN_API_KEY"],
)


def answer(question: str) -> str:
    response = client.chat.completions.create(
        model=MODEL,
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    import sys

    print(answer(" ".join(sys.argv[1:]) or "Do you charge for shipping?"))
