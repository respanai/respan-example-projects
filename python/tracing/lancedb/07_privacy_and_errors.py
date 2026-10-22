from tempfile import TemporaryDirectory

import lancedb
from _shared import rows, run_scenario
from opentelemetry import context
from respan_tracing.constants.context_constants import ENABLE_CONTENT_TRACING_KEY


async def run():
    with TemporaryDirectory() as path:
        table = lancedb.connect(path).create_table("documents", rows())
        try:
            table.search().where("invalid ! SQL").to_list()
        except (ValueError, RuntimeError) as error:
            error_type = type(error).__name__
        db = await lancedb.connect_async(path)
        at = await db.open_table("documents")
        reader = await at.query().limit(2).to_batches()
        token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        try:
            await reader.__anext__()
        finally:
            context.detach(token)
        await reader.read_all()
        db.close()
        token = context.attach(context.set_value(ENABLE_CONTENT_TRACING_KEY, False))
        query = table.search()
        context.detach(token)
        private = query.limit(20).to_list()
        return {"private_rows": len(private), "native_error_type": error_type}


if __name__ == "__main__":
    run_scenario("lancedb_privacy_and_errors", run)
