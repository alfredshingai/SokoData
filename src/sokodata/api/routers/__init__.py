from .catalog import router as catalog_router
from .commodities import router as commodities_router
from .demographics import router as demographics_router
from .economy import router as economy_router
from .education import router as education_router
from .energy import router as energy_router
from .environment import router as environment_router
from .finance import router as finance_router
from .gender import router as gender_router
from .geospatial import router as geospatial_router
from .governance import router as governance_router
from .health import router as health_router
from .ict import router as ict_router
from .insights import router as insights_router
from .labour import router as labour_router
from .markets import router as markets_router
from .meta import router as meta_router
from .mining import router as mining_router
from .poverty import router as poverty_router
from .prices import router as prices_router
from .tourism import router as tourism_router
from .trade import router as trade_router
from .transport import router as transport_router
from .water import router as water_router
from .webhooks import router as webhooks_router
from .webhooks import whatsapp_router
from .analyze import router as analyze_router
from .agriculture import router as agriculture_router
from .aid import router as aid_router
from .auth import router as auth_router
from .climate import router as climate_router
from .export import router as export_router
from .gender import router as gender_router
from .geospatial import router as geospatial_router
from .tourism import router as tourism_router
from .trade import router as trade_router
from .transport import router as transport_router
from .webhooks import whatsapp_router

catalog = catalog_router
commodities = commodities_router
demographics = demographics_router
economy = economy_router
education = education_router
energy = energy_router
environment = environment_router
finance = finance_router
gender = gender_router
geospatial = geospatial_router
governance = governance_router
health = health_router
ict = ict_router
insights = insights_router
labour = labour_router
markets = markets_router
meta = meta_router
mining = mining_router
poverty = poverty_router
prices = prices_router
tourism = tourism_router
trade = trade_router
transport = transport_router
water = water_router
webhooks = webhooks_router
agriculture = agriculture_router
aid = aid_router
auth = auth_router
climate = climate_router
export = export_router
tourism = tourism_router
trade = trade_router
transport = transport_router

__all__ = [
    "catalog", "commodities", "demographics", "economy", "education", "energy",
    "environment", "finance", "gender", "geospatial", "governance", "health",
    "ict", "insights", "labour", "markets", "meta", "mining", "poverty", "prices",
    "tourism", "trade", "transport", "water", "webhooks", "whatsapp_router",
    "agriculture", "aid", "auth", "analyze", "climate", "export", "tourism", "trade",
    "transport", "webhooks",
]