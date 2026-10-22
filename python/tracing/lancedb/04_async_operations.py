from tempfile import TemporaryDirectory

import lancedb
from _shared import rows, run_scenario
from lancedb.index import BTree


async def run():
    with TemporaryDirectory() as path:
        db = await lancedb.connect_async(path)
        await db.create_table("documents", rows())
        table = await db.open_table("documents")
        await table.add(rows(1))
        await table.update(where="id=0", updates={"text": "updated native row"})
        await table.delete("id=19")
        merge = table.merge_insert("id")
        await (
            merge.when_matched_update_all()
            .when_not_matched_insert_all()
            .execute(rows(2))
        )
        await table.create_index("id", config=BTree())
        await table.optimize()
        vector = (await table.search([0.0] * 4)).limit(20)
        result = await vector.to_list()
        arrow = await table.query().limit(20).to_arrow()
        frame = await table.query().limit(20).to_pandas()
        plan = await (await table.search([0.0] * 4)).limit(20).explain_plan()
        names = await db.table_names()
        await db.drop_table("documents")
        db.close()
        return {
            "rows": len(result),
            "arrow_rows": arrow.num_rows,
            "pandas_rows": len(frame),
            "plan": bool(plan),
            "tables": len(names),
        }


if __name__ == "__main__":
    run_scenario("lancedb_async_operations", run)
