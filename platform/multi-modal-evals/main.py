from example_workflows.multi_modal_tool_evals.logs import get_logs
from example_workflows.multi_modal_tool_evals.constants import (
    EVAL_RUN_FILTER_KEY,
    EVAL_RUN_ID,
)
from datetime import datetime, timedelta

logs = get_logs(
    start_time=datetime.now() - timedelta(days=1),
    end_time=datetime.now(),
    filters={
        EVAL_RUN_FILTER_KEY: {
            "value": EVAL_RUN_ID,
        },
    },
)



