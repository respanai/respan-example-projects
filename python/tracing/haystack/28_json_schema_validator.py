"""One-script example for JsonSchemaValidator."""

from _shared import configure_respan, finish_respan, print_result


def run_json_schema_validator_example():
    respan = configure_respan("haystack-json-schema-validator")
    try:
        from haystack.components.validators import JsonSchemaValidator
        from haystack.dataclasses import ChatMessage

        schema = {
            "type": "object",
            "properties": {"answer": {"type": "string"}},
            "required": ["answer"],
        }
        validator = JsonSchemaValidator(schema)
        result = {
            "valid": validator.run([ChatMessage.from_assistant('{"answer": "Paris"}')]),
            "invalid": validator.run(
                [ChatMessage.from_assistant('{"wrong": "Paris"}')]
            ),
        }
        print_result("JsonSchemaValidator", result)
        return result
    finally:
        finish_respan(respan)


if __name__ == "__main__":
    run_json_schema_validator_example()
