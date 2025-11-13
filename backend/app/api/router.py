from fastapi import APIRouter

from .v1.endpoints import (
    auth,
    bot,
    bots,
    broadcasts,
    channels,
    dashboard,
    health,
    payments,
    promo_codes,
    settings,
    subscribers,
    subscription_plans,
)

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(subscribers.router, prefix="/subscribers", tags=["Subscribers"])
api_router.include_router(payments.router, prefix="/payments", tags=["Payments"])
api_router.include_router(subscription_plans.router, prefix="/plans", tags=["Plans"])
api_router.include_router(promo_codes.router, prefix="/promo-codes", tags=["PromoCodes"])
api_router.include_router(bots.router, prefix="/bots", tags=["Bots"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(channels.router, prefix="/channels", tags=["Channels"])
api_router.include_router(broadcasts.router, prefix="/broadcasts", tags=["Broadcasts"])
api_router.include_router(bot.router, prefix="/bot", tags=["Bot"])

