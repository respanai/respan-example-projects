from tempfile import TemporaryDirectory

import lancedb
import pyarrow as pa
from _shared import rows, run_scenario


async def run():
    with TemporaryDirectory() as path:
        table = lancedb.connect(path).create_table("documents", rows())
        reader = table.search().limit(20).to_batches(batch_size=3)
        assert type(reader) is pa.RecordBatchReader
        batch = reader.read_next_batch()
        reader.close()
        with table.search().limit(20).to_batches() as complete:
            total = complete.read_all().num_rows
        db = await lancedb.connect_async(path)
        at = await db.open_table("documents")
        first = await at.query().limit(20).to_batches(max_batch_length=3)
        second = await at.query().limit(20).to_batches(max_batch_length=3)
        one = await first.read_all()
        two = [b async for b in second]
        db.close()
        return {
            "first_sync_batch": batch.num_rows,
            "sync_all": total,
            "async_all": sum(b.num_rows for b in one),
            "async_iteration": sum(b.num_rows for b in two),
        }


if __name__ == "__main__":
    run_scenario("lancedb_native_readers", run)
