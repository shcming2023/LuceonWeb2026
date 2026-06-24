from .upload import router as upload_router
from .files import router as files_router
from .materials import router as materials_router
from .parsed import router as parsed_router
from .review import router as review_router
from .runtime_settings import router as runtime_settings_router
from .settings import router as settings_router
from .health import router as health_router
from .auth import router as auth_router
from . import stats

routers = [
    auth_router,
    upload_router,
    files_router,
    materials_router,
    parsed_router,
    review_router,
    runtime_settings_router,
    settings_router,
    health_router,
    stats.router,  # 注册 stats 路由
]
