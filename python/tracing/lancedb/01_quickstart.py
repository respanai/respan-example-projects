from tempfile import TemporaryDirectory

import lancedb
from _shared import rows, run_scenario


def run():
    with TemporaryDirectory() as path:
        db = lancedb.connect(path)
        table = db.create_table("documents", rows(3))
        table.add(rows(1))
        matches = table.search([0.0] * 4).select(["id", "text"]).limit(2).to_list()
        names = db.table_names()
        db.drop_table("documents")
        return {"tables": names, "matches": len(matches)}


if __name__ == "__main__":
    run_scenario("lancedb_quickstart", run)
