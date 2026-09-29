"""SokoData HTTP API (FastAPI) - Open Data Commons for Zimbabwe.

Run locally:
    uvicorn sokodata.api.main:app --reload
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from sokodata import __version__
from sokodata.api.routers import (
    agriculture, aid, auth, catalog, climate, commodities, demographics, economy,
    education, energy, environment, export, finance, gender, geospatial, governance,
    health as health_router, ict, insights, labour, markets, meta, mining, poverty,
    prices, tourism, trade, transport, water, webhooks, whatsapp_router,
)
from sokodata.config import DATA_CREDIT, DB_PATH
from sokodata.datasets.markets.store import connect

log = logging.getLogger(__name__)


def load_prices_frame(conn) -> pd.DataFrame:
    """Load the full prices table into pandas for in-memory analytics."""
    query = """
        SELECT p.date, p.market_id, m.market, p.commodity_id, p.commodity,
               p.category, p.unit, p.priceflag, p.pricetype, p.currency,
               p.price, p.usdprice
        FROM prices p JOIN markets m ON m.market_id = p.market_id
        ORDER BY p.date
    """
    try:
        df = pd.read_sql(query, conn, parse_dates=["date"])
        return df
    except Exception:
        return pd.DataFrame()


def create_app(db_path: Path | str | None = None) -> FastAPI:
    path = Path(db_path) if db_path else DB_PATH

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        conn = connect(path, read_only=True, check_same_thread=False)
        try:
            app.state.conn = conn
            app.state.prices = load_prices_frame(conn)
            log.info("loaded %d price rows from %s", len(app.state.prices), path)
        except Exception:
            conn.close()
            raise
        yield
        app.state.conn.close()

    app = FastAPI(
        title="SokoData API - Open Data Commons for Zimbabwe",
        description=(
            "Open data commons for Zimbabwe: market prices, economy, climate and more. "
            "See /v1/catalog for all datasets. "
            "Market prices: World Food Programme Price Database via HDX (CC BY-IGO)."
        ),
        version=__version__,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET"],
        allow_headers=["*"],
    )

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse(url="/docs")

    @app.get("/health", response_model=None, tags=["meta"])
    def health():
        from sokodata.api.schemas import Health
        from sokodata.datasets.markets.analysis.seasonal import coverage

        cov = coverage(app.state.prices) if app.state.prices is not None and not app.state.prices.empty else {"observations": 0, "markets": 0, "commodities": 0, "first_date": None, "last_date": None}
        return Health(
            status="ok" if app.state.prices is not None else "empty",
            version=__version__,
            coverage=cov,
            data_credit=DATA_CREDIT,
        )

    app.include_router(catalog, prefix="/v1")
    app.include_router(markets, prefix="/v1")
    app.include_router(commodities, prefix="/v1")
    app.include_router(prices, prefix="/v1")
    app.include_router(insights, prefix="/v1")
    app.include_router(economy, prefix="/v1")
    app.include_router(climate, prefix="/v1")
    app.include_router(demographics, prefix="/v1")
    app.include_router(agriculture, prefix="/v1")
    app.include_router(health_router, prefix="/v1")
    app.include_router(education, prefix="/v1")
    app.include_router(energy, prefix="/v1")
    app.include_router(water, prefix="/v1")
    app.include_router(transport, prefix="/v1")
    app.include_router(mining, prefix="/v1")
    app.include_router(governance, prefix="/v1")
    app.include_router(trade, prefix="/v1")
    app.include_router(labour, prefix="/v1")
    app.include_router(environment, prefix="/v1")
    app.include_router(poverty, prefix="/v1")
    app.include_router(ict, prefix="/v1")
    app.include_router(finance, prefix="/v1")
    app.include_router(tourism, prefix="/v1")
    app.include_router(aid, prefix="/v1")
    app.include_router(gender, prefix="/v1")
    app.include_router(geospatial, prefix="/v1")
    app.include_router(meta, prefix="/v1")
    app.include_router(auth, prefix="/v1")
    app.include_router(export, prefix="/v1")
    app.include_router(whatsapp_router)
    app.include_router(webhooks)
    return app


app = create_app()


def serve() -> None:
    uvicorn.run("sokodata.api.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    serve()
