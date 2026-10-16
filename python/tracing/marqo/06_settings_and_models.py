"""Actual released Marqo clients; deterministic native HTTP by default."""

from _shared import marqo_client, run_case


def action(provider, local):
    import inspect

    import marqo

    with marqo_client() as (client, _requests):
        index = client.index("docs")
        assert index.get_settings()["normalizeEmbeddings"] is False
        assert index.get_stats()["numberOfDocuments"] == 0
        assert client.get_indexes()["results"] == []
        kwargs = (
            {"model_device": "cpu"}
            if "model_device"
            in inspect.signature(marqo.index.Index.eject_model).parameters
            else {}
        )
        index.eject_model("actual-model", **kwargs)
    return "native settings/stats/listing and compatible model ejection arguments"


if __name__ == "__main__":
    run_case("marqo_settings_models", action)
