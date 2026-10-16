"""Controlled released Ragas APIs; provider calls are local unless explicitly exported."""

from __future__ import annotations

import os

os.environ["RAGAS_DO_NOT_TRACK"] = "true"
import asyncio

import ragas
from _shared import run_case
from ragas.backends import InMemoryBackend
from ragas.dataset import Dataset


async def calls(asynchronous):
    backend = InMemoryBackend()
    rows = Dataset(name="controlled_rows", backend=backend)
    rows.append({"value": 0})
    rows.append({"value": 1})
    result = {"zero": 0, "flag": False, "empty": ""}
    if asynchronous:

        @ragas.experiment(backend=backend)
        async def controlled(row):
            return result
    else:

        @ragas.experiment(backend=backend)
        def controlled(row):
            return result

    assert await controlled({"value": 0}) is result
    dataset = await controlled.arun(rows, name="controlled_experiment")
    assert len(dataset) == 2 and backend.load_experiment("controlled_experiment") == [
        result,
        result,
    ]
    return dataset


def action(provider, local):
    asyncio.run(calls(False))
    asyncio.run(calls(True))
    return "native sync/async application experiment callbacks, direct calls and dataset arun with false/zero/empty"


if __name__ == "__main__":
    run_case("ragas_experiments", action)
