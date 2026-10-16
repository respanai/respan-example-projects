"""Extract a typed response with the async Instructor client."""

from __future__ import annotations

import asyncio

from _respan_instructor import create_respan_instructor_client, workflow
from pydantic import BaseModel
from respan_tracing.exporters import propagate_attributes


class ProjectBrief(BaseModel):
    title: str
    owner: str
    milestones: list[str]
    risk: str


@workflow(name="instructor_example_05_async_create")
async def create_project_brief(client, scenario: str) -> ProjectBrief:
    return await client.create(
        response_model=ProjectBrief,
        messages=[
            {
                "role": "user",
                "content": (
                    "Build a project brief. The title must be exactly "
                    "'Respan Instructor tracing launch'. Owner is Jordan. "
                    "Milestones are SDK validation, docs update, and release "
                    "intent. The main risk is schema drift."
                ),
            }
        ],
    )


async def run_async_create_example() -> None:
    respan, client = create_respan_instructor_client(
        app_name="instructor-async-create",
        async_client=True,
        payload={
            "title": "Respan Instructor tracing launch",
            "owner": "Jordan",
            "milestones": ["SDK validation", "Docs update", "Release intent"],
            "risk": "Schema drift",
        },
    )

    try:
        with propagate_attributes(
            thread_identifier="instructor_example_05_async_create",
            metadata={
                "example_script": "05_async_create.py",
                "instructor_api": "async_create",
            },
        ):
            project_brief = await create_project_brief(
                client,
                "build a deterministic project brief",
            )

        print(dict(project_brief))
    finally:
        await client.client.close()
        respan.shutdown()


if __name__ == "__main__":
    asyncio.run(run_async_create_example())
