from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, BaseSettings, HttpUrl


class Settings(BaseModel):
    jwt_secret: str
    github_oauth_settings: _GithubOAuthSettings


class _Settings(BaseSettings):
    jwt_secret: str = "secret"


class _GithubOAuthSettings(BaseSettings):
    github_oauth_userinfo_endpoint: Optional[HttpUrl] = None
    github_oauth_authorize_url: Optional[HttpUrl] = None


Settings.update_forward_refs()
settings = Settings(jwt_secret=_Settings().jwt_secret, github_oauth_settings=_GithubOAuthSettings())

__all__ = ['settings']
