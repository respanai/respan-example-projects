from tempfile import TemporaryDirectory

import lancedb
from _shared import rows, run_scenario


def run():
    with TemporaryDirectory() as path:
        db = lancedb.connect(path)
        db.create_table("documents", rows())
        table = db.open_table("documents")
        table.add(rows(1))
        table.update(where="id=0", values={"text": "updated native row"})
        table.delete("id=19")
        table.merge_insert(
            "id"
        ).when_matched_update_all().when_not_matched_insert_all().execute(rows(2))
        table.create_scalar_index("id")
        table.optimize()
        names = db.table_names()
        if hasattr(db, "list_tables"):
            db.list_tables()
        result = table.search().limit(100).to_list()
        db.drop_table("documents")
        return {"tables": len(names), "rows": len(result)}


if __name__ == "__main__":
    run_scenario("lancedb_tables_and_merge", run)
