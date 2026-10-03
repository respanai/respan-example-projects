"""One-script example for MetadataRouter."""

from _shared import configure_respan, finish_respan, print_result, sample_documents


def run_metadata_router_example():
    respan = configure_respan("haystack-metadata-router")
    try:
        from haystack.components.routers import MetadataRouter

        rules = {
            "programming": {
                "field": "meta.kind",
                "operator": "==",
                "value": "programming",
            },
            "cooking": {"field": "meta.kind", "operator": "==", "value": "cooking"},
        }
        result = MetadataRouter(rules).run(sample_documents())
        print_result("MetadataRouter", result)
        return result
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    run_metadata_router_example()
