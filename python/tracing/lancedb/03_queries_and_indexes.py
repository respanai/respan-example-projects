from tempfile import TemporaryDirectory

import lancedb
from _shared import rows, run_scenario


def run():
    with TemporaryDirectory() as path:
        table = lancedb.connect(path).create_table("documents", rows())
        table.create_fts_index("text", use_tantivy=False)
        vector = (
            table.search([0.0] * 4)
            .where("id>=0")
            .select(["id", "vector", "flag", "zero"])
            .limit(20)
        )
        arrow = vector.to_arrow()
        frame = table.search().limit(20).to_pandas()
        plan = table.search([0.0] * 4).limit(20).explain_plan()
        fts = table.search("native", query_type="fts").limit(20).to_list()
        hybrid = (
            table.search(query_type="hybrid")
            .vector([0.0] * 4)
            .text("native")
            .limit(2)
            .to_list()
        )
        return {
            "arrow_rows": arrow.num_rows,
            "pandas_rows": len(frame),
            "fts": len(fts),
            "hybrid": len(hybrid),
            "plan": bool(plan),
        }


if __name__ == "__main__":
    run_scenario("lancedb_queries_and_indexes", run)
