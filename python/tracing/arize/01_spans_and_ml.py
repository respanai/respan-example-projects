"""Read historical span payloads and submit a native protobuf Future upload."""

from _fixture import PROJECT_ID, SPACE_ID
from _shared import example, print_result
from arize.ml.types import Embedding, Environments, ModelTypes


def main():
    with example("01_spans_and_ml") as client:
        spans = client.spans.list(project=PROJECT_ID)
        print_result("Native spans", spans)
        future = client.ml.log_stream(
            space_id=SPACE_ID,
            model_name="fixture-regression",
            model_type=ModelTypes.REGRESSION,
            environment=Environments.PRODUCTION,
            prediction_label=1.0,
            embedding_features={
                "controlled": Embedding(vector=[float(i) for i in range(3072)])
            },
        )
        assert future.result(timeout=5).status_code == 202
        print_result("Native upload handle", future)


if __name__ == "__main__":
    main()
