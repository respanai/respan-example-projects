"""Verify that local fixtures construct the installed IBM SDK and parse native SSE."""

from _shared import GEN, close, native
from ibm_watsonx_ai.foundation_models import Embeddings, ModelInference


def test_actual_native_local_transport_and_resource_contract():
    c, m, e, requests, _responses, body, *_ = native(frames=[GEN])
    assert type(m) is ModelInference and type(e) is Embeddings
    try:
        assert (
            list(
                m.generate_text_stream(prompt="Controlled fixture.", raw_response=True)
            )
            == [GEN]
            and body.closed == 1
            and len(requests) == 1
        )
    finally:
        close(c)
