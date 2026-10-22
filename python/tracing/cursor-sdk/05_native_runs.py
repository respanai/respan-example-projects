from _fixtures import Fixture, events
from _shared import tracing
from cursor_sdk import SendOptions


def main():
    with tracing("native-runs") as (_, memory):
        seen = []
        fixture = Fixture(
            rows=events(
                tools=True,
                modern=True,
                usage={
                    "inputTokens": 7,
                    "outputTokens": 3,
                    "totalTokens": 10,
                    "cacheReadTokens": 0,
                    "reasoningTokens": 2,
                },
            )
        )
        with fixture.client() as client:
            agent = fixture.agent(client)
            run = agent.send(
                "Fixture prompt",
                SendOptions(
                    on_step=seen.append,
                    cloud={"env_vars": {"FIXTURE_TOKEN": "synthetic-secret"}},
                    model={
                        "id": "composer-fixture",
                        "params": [{"id": "effort", "value": "high"}],
                    },
                ),
            )
            assert run.wait().result == "Fixture completion" and len(seen) == 1
        assert len(memory.get_finished_spans()) == 2


if __name__ == "__main__":
    main()
