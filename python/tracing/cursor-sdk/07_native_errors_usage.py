from _fixtures import Fixture, events
from _shared import tracing
from cursor_sdk.errors import CursorSDKError


def main():
    with tracing("native-errors-usage") as (_, memory):
        with Fixture(rows=events(status="error")).client() as client:
            result = Fixture.agent(client).send("Fixture failed run").wait()
            assert result.status == "error"
        with Fixture(error=503).client() as client:
            try:
                Fixture.agent(client).send("Fixture transport failure")
            except CursorSDKError as error:
                assert error.status_code == 503
            else:
                raise AssertionError("Controlled transport error required")
        with Fixture().client() as client:
            agent = Fixture.agent(client)
            if hasattr(agent, "get_usage"):
                assert agent.get_usage().usage.total_tokens == 10
            else:
                print("SKIP billed usage API: absent from native minimum1.0.24")
        assert len(memory.get_finished_spans()) in (2, 3)


if __name__ == "__main__":
    main()
