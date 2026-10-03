"""Small local validator: no Hub credentials, downloads, or remote models."""

from guardrails.validators import FailResult, PassResult, Validator, register_validator


@register_validator(name="respan-fixture-accepted", data_type="string")
class AcceptedText(Validator):
    def validate(self, value, metadata):
        if value == "fixture accepted":
            return PassResult()
        return FailResult(
            error_message="Expected fixture accepted", fix_value="fixture accepted"
        )
