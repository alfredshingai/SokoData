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
from sokodata.api.routers import agriculture, catalog, climate, commodities, demographics, economy, education, energy, governance, health as health_router, insights, labour, markets, mining, prices, trade, transport, water, webhooks
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

    app.include_router(catalog.router, prefix="/v1")
    app.include_router(markets.router, prefix="/v1")
    app.include_router(commodities.router, prefix="/v1")
    app.include_router(prices.router, prefix="/v1")
    app.include_router(insights.router, prefix="/v1")
    app.include_router(economy.router, prefix="/v1")
    app.include_router(climate.router, prefix="/v1")
    app.include_router(demographics.router, prefix="/v1")
    app.include_router(agriculture.router, prefix="/v1")
    app.include_router(health_router.router, prefix="/v1")
    app.include_router(education.router, prefix="/v1")
    app.include_router(energy.router, prefix="/v1")
    app.include_router(water.router, prefix="/v1")
    app.include_router(transport.router, prefix="/v1")
    app.include_router(mining.router, prefix="/v1")
    app.include_router(governance.router, prefix="/v1")
    app.include_router(trade.router, prefix="/v1")
    app.include_router(labour.router, prefix="/v1")
    app.include_router(webhooks.router)
    return app


app = create_app()


def serve() -> None:
    uvicorn.run("sokodata.api.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    serve()
