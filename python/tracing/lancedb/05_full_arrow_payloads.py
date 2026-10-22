from tempfile import TemporaryDirectory

import lancedb
import pyarrow as pa
from _shared import rows, run_scenario


def run():
    with TemporaryDirectory() as path:
        data = pa.Table.from_pylist(rows(75, 5001))
        schema = data.schema.with_metadata({b"api_key": b"controlled", b"zero": b"0"})
        table = lancedb.connect(path).create_table("full", data=data, schema=schema)
        result = table.search().limit(75).to_arrow()
        empty = table.search().where("id<0").limit(75).to_list()
        return {
            "rows": result.num_rows,
            "dimensions": len(result["vector"][0].as_py()),
            "empty": len(empty),
        }


if __name__ == "__main__":
    run_scenario("lancedb_full_arrow_payloads", run)
