import logging
import urllib.parse

from typing import List, Optional

import httpx
import jwt

from fastapi import Cookie, Depends, Query, Request
from fastapi.responses import PlainTextResponse, RedirectResponse

from forwardauth_middleware.models import ForwardRequestHeaders, get_forward_request_headers
from forwardauth_middleware.settings import settings

logger = logging.getLogger()


async def authentication_by_github(
    request: Request,
    use_whitelist: Optional[bool] = Query(True,
                                          alias='use_whitelist'),
    whitelist: List[str] = Query(None,
                                 alias='whitelist'),
    frh: ForwardRequestHeaders = Depends(get_forward_request_headers),
    cookie_field: str = Query('github_oauth_sig',
                              alias='auth_cookie_field'),
    authorization: Optional[str] = Cookie(None,
                                          alias='Authorization'),
    samesite: str = Query('none'),
):
    """基于 GithubOAuth的身份验证.

    在 GitHub OAuth 授权通过后, 重定向所携带的 code 参数兑换获取用户信息, 并将用户信息写入 Cookie, 作为凭证.

    首次认证用户流程

    traefik -> middleware -> authorize_url -> traefik -> middleware(http call) -> traefik -> middleware -> endpoint.
    1. traefik 代理接受请求, 调用 forwardauth 中间件
    2. forwardauth 中间件基于 Cookie 进行身份验证
    3. forwardauth 验证信息失败, 重定向到 Github OAuth 授权页.
    4. Github OAuth授权成功, 重定向回 traefik 代理处理请求
    5. traefik 代理接受请求, 调用 forwardauth 中间件
    6. forwardauth 中间件基于 GithubOAuth 回传的 code, 调用指定的 endpoint, 获取用户信息
    7. forwardauth 中间件将用户信息编码, 通过 307 重定向写入 cookie, 跳转回traefik 代理
    8. traefik 代理接受请求, 调用 forwardauth 中间件
    9. forwardauth 基于 Cookie 认证用户身份, 放行请求
    10. traefik 代理转发请求到提供服务的 endpoint.

    已认证用户流程

    traefik -> middleware -> endpoint.
    1. traefik 代理接受请求, 调用 forwardauth 中间件
    2. forwardauth 中间件基于 Cookie 认证用户身份, 放行请求
    3. traefik 代理转发请求到提供服务的 endpoint.

    认证失败流程

    traefik -> middleware.
    1. traefik 代理接受请求, 调用 forwardauth 中间件
    2. forwardauth 中间件基于 Cookie 认证用户身份, 验证失败, 拒绝放行
    3. traefik 代理停止转发请求, 将 forwardauth 中间件的响应返回
    \f
    traefik2.8版本不支持将指定标头添加到最终的响应内.

    对于需要刷新客户端 cookie 的操作, 需要用 307 重定向, 将 Set-Cookie 写进客户端.

    Args:
        whitelist (List[str], optional): _description_. Defaults to Query(None, alias='whitelist').
        forward_request_headers (ForwardRequestHeaders, optional): _description_. Defaults to Depends(get_forward_request_headers).
        key (Optional[str], optional): _description_. Defaults to Cookie(None, alias='cookie_key').

    Returns:
        _type_: _description_
    """
    if frh.method.upper() == 'OPTIONS':
        return PlainTextResponse()

    if settings.github_oauth_settings.github_oauth_authorize_url is None or settings.github_oauth_settings.github_oauth_userinfo_endpoint is None:
        logger.warning("未配置github oauth 相关信息")
        return PlainTextResponse('请联系管理员配置中间件信息', status_code=500)

    if use_whitelist and whitelist is None:
        return PlainTextResponse('请联系管理员配置白名单', status_code=401)

    logger.debug((f"whitelist: \n{whitelist}\n"
                  f"forward request headers:\n{frh}"))

    code: Optional[str] = None
    params = urllib.parse.parse_qs(urllib.parse.urlsplit(frh.uri).query)
    if 'code' in params:
        code = params['code'][0]

    authorization = request.cookies.get(cookie_field)
    # 验证身份有效性
    if authorization:
        data = jwt.decode(authorization, settings.jwt_secret, algorithms=["HS256"])
        username = data['username']
        if use_whitelist and username not in whitelist:
            return PlainTextResponse("该用户没有访问权限", status_code=401)
        return PlainTextResponse()

    if code is not None:
        # 用户授权认证成功后回到本地, 并刷新 cookie
        endpoint = settings.github_oauth_settings.github_oauth_userinfo_endpoint
        client = httpx.AsyncClient()
        res = await client.get(endpoint, params={'code': code})
        if res.status_code != 200:
            return PlainTextResponse(res.text, status_code=res.status_code)

        payload = res.json()
        assert 'username' in payload, payload
        sig = jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

        # traefik v2.8 目前不支持将 forwardauth 中间件的响应头写入返回给客户端的响应
        # 通过一次临时重定向, 将 Set-Cookie 写进客户端
        urlsplit_result = urllib.parse.urlsplit(frh.uri)
        params = urllib.parse.parse_qs(urlsplit_result.query)
        params.pop('code', None)
        query = urllib.parse.urlencode(params, doseq=True)
        uri = f'{urlsplit_result.path}?{query}' if query else f'{urlsplit_result.path}'
        redirect_url = f'{frh.protocol}://{frh.host}{uri}'

        logger.debug(f"authentication passed. final redirect url: {redirect_url}")

        response = RedirectResponse(redirect_url)
        response.set_cookie(cookie_field, sig, secure=True, samesite=samesite)
        return response
    # 重定向到认证服务

    else:
        authorize_url = settings.github_oauth_settings.github_oauth_authorize_url
        redirect_url = f'{frh.protocol}://{frh.host}{frh.uri}'

        params = {'redirect_url': redirect_url}
        authorize_url = f"{authorize_url}?{urllib.parse.urlencode(params)}"
        logger.debug(f"redirect_url: {redirect_url}")
        logger.debug(f"authorize_url: {authorize_url}")
        return RedirectResponse(authorize_url)
