from _shared import GEN, close, native, run_case
from ibm_watsonx_ai.foundation_models.schema import TextGenParameters


def action(provider):
    c, m, *_ = native(GEN)
    try:
        assert (
            m.generate(
                prompt="Controlled generation.",
                params=TextGenParameters(temperature=0, max_new_tokens=0),
            )
            == GEN
        )
        assert (
            m.generate_text(prompt="Controlled text.")
            == GEN["results"][0]["generated_text"]
        )
        results = m.generate(prompt=["Controlled one.", "Controlled two."])
        assert len(results) == 2
        return "generation, convenience text, and native batch"
    finally:
        close(c)


if __name__ == "__main__":
    run_case("watsonx_generation", action)
