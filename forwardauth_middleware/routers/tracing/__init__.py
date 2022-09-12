from fastapi import APIRouter

from forwardauth_middleware.routers.tracing.settraceid import settraceid

router = APIRouter(prefix='/tracing', tags=['forwardauth-tracing'])
router.add_api_route('/settraceid', settraceid)

__all__ = ['router']
