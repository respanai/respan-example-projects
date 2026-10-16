from _native import Native
from _shared import Runtime

r = Runtime("prediction_lifecycle")
n = Native("controlled final output")
n.statuses = ["starting", "processing", "succeeded"]
try:
    with r.workflow():
        prediction = n.client.predictions.create(
            model="owner/model", input={"prompt": "Poll actual prediction"}
        )
        assert prediction.status == "starting"
        assert prediction.wait() is None and prediction.output == n.output
        assert prediction.reload() is None
        assert prediction.cancel() is None
        assert n.client.predictions.get("controlled").id == "controlled"
        assert n.client.predictions.list().results[0].id == "controlled"
        n.client.predictions.cancel("controlled")
        n.client.models.predictions.create(
            model="owner/model", input={"prompt": "Model route"}
        )
        n.client.deployments.predictions.create(
            deployment="owner/deployment", input={"prompt": "Deployment route"}
        )
        events = prediction.stream()
        assert next(events).data == "chunk-0"
        events.close()
finally:
    n.close()
    r.close()
