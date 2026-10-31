"""Routers for the SokoData API — one per dataset/feature, re-exported by name."""

from .agriculture import router as agriculture
from .aid import router as aid
from .analyze import router as analyze
from .auth import router as auth
from .catalog import router as catalog
from .climate import router as climate
from .commodities import router as commodities
from .demographics import router as demographics
from .economy import router as economy
from .education import router as education
from .energy import router as energy
from .environment import router as environment
from .export import router as export
from .finance import router as finance
from .gender import router as gender
from .geospatial import router as geospatial
from .governance import router as governance
from .health import router as health
from .ict import router as ict
from .indicators import router as indicators
from .insights import router as insights
from .labour import router as labour
from .markets import router as markets
from .meta import router as meta
from .mining import router as mining
from .poverty import router as poverty
from .prices import router as prices
from .tourism import router as tourism
from .trade import router as trade
from .transport import router as transport
from .water import router as water
from .webhooks import router as webhooks
from .webhooks import whatsapp_router

__all__ = [
    "agriculture",
    "aid",
    "analyze",
    "auth",
    "catalog",
    "climate",
    "commodities",
    "demographics",
    "economy",
    "education",
    "energy",
    "environment",
    "export",
    "finance",
    "gender",
    "geospatial",
    "governance",
    "health",
    "ict",
    "indicators",
    "insights",
    "labour",
    "markets",
    "meta",
    "mining",
    "poverty",
    "prices",
    "tourism",
    "trade",
    "transport",
    "water",
    "webhooks",
    "whatsapp_router",
]
