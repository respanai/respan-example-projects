"""Deterministic workflows used by the Temporal examples."""

from __future__ import annotations

from datetime import timedelta

from temporalio import activity, workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError


@activity.defn
async def compose_greeting(name: str) -> str:
    return f"Hello, {name}!"


@activity.defn
async def fail_once(reason: str) -> None:
    raise ApplicationError(reason, non_retryable=True)


@workflow.defn
class GreetingWorkflow:
    @workflow.run
    async def run(self, name: str) -> str:
        return await workflow.execute_activity(
            compose_greeting,
            name,
            start_to_close_timeout=timedelta(seconds=10),
        )


@workflow.defn
class FailingWorkflow:
    @workflow.run
    async def run(self, reason: str) -> None:
        await workflow.execute_activity(
            fail_once,
            reason,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_attempts=1),
        )


@workflow.defn
class ApprovalWorkflow:
    def __init__(self) -> None:
        self._approved = False

    @workflow.run
    async def run(self, topic: str) -> str:
        await workflow.wait_condition(lambda: self._approved)
        return f"approved:{topic}"

    @workflow.signal
    async def approve(self) -> None:
        self._approved = True

    @workflow.query
    def status(self) -> str:
        return "approved" if self._approved else "pending"


@activity.defn
async def echo_payload(value: dict) -> dict:
    return value


@workflow.defn
class PayloadWorkflow:
    @workflow.run
    async def run(self, value: dict) -> dict:
        return await workflow.execute_activity(
            echo_payload, value, start_to_close_timeout=timedelta(seconds=10)
        )
