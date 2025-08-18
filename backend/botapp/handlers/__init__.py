from aiogram import Router
from . import start, balance, deposit, miners, withdraw, admin, referrals, about

def setup_routers() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(miners.router)
    router.include_router(balance.router)
    router.include_router(deposit.router)
    router.include_router(withdraw.router)
    router.include_router(referrals.router)
    router.include_router(about.router)
    return router


def setup_admin_routers() -> Router:
    router = Router()
    router.include_router(admin.router)
    return router