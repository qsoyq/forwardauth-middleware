from fastapi import Header
from pydantic import BaseModel


class ForwardRequestHeaders(BaseModel):
    method: str
    protocol: str
    host: str
    uri: str
    ip: str


async def get_forward_request_headers(
    method: str = Header(...,
                         alias='X-Forwarded-Method'),
    protocol: str = Header(...,
                           alias='X-Forwarded-Proto'),
    host: str = Header(...,
                       alias='X-Forwarded-Host'),
    uri: str = Header(...,
                      alias='X-Forwarded-Uri'),
    ip: str = Header(...,
                     alias='X-Forwarded-For')
):
    return ForwardRequestHeaders(method=method, protocol=protocol, host=host, uri=uri, ip=ip)
