from typing import Optional

from fastapi import Header
from fastapi.responses import PlainTextResponse

from forwardauth_middleware.utils.snowflake import Snowflake


async def settraceid(x_trace_id: Optional[str] = Header(None, alias='X-Trace-Id')):
    """为请求添加全局跟踪 ID
    \f
    Args:
        x_trace_id (Optional[str], optional): _description_. Defaults to Header(None, alias='X-Trace-Id').
    """
    headers = {}
    msgid = Snowflake().generate()
    if x_trace_id is None:
        headers["X-Trace-Id"] = str(msgid)
    return PlainTextResponse(headers=headers)
