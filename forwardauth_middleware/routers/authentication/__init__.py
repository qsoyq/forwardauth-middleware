from fastapi import APIRouter

from forwardauth_middleware.routers.authentication.github_oauth import authentication_by_github

router = APIRouter(prefix='/authentication', tags=['forwardauth-authentication'])
router.add_api_route('/github', authentication_by_github)

__all__ = ['router']
