"""SokoData HTTP API (FastAPI).

Run locally:
    uvicorn sokodata.api.main:app --reload
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

import pandas as pd
import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from sokodata import __version__
from sokodata.analysis import seasonal
from sokodata.api.routers import commodities, insights, markets, prices, webhooks
from sokodata.config import DATA_CREDIT, DB_PATH
from sokodata.etl.store import connect

log = logging.getLogger(__name__)


def load_prices_frame(conn) -> pd.DataFrame:
    """Load the full prices table into pandas for in-memory analytics.

    At Zimbabwe scale this is ~27k rows; re-run the ETL to refresh.
    """
    query = """
        SELECT p.date, p.market_id, m.market, p.commodity_id, p.commodity,
               p.category, p.unit, p.priceflag, p.pricetype, p.currency,
               p.price, p.usdprice
        FROM prices p JOIN markets m ON m.market_id = p.market_id
        ORDER BY p.date
    """
    df = pd.read_sql(query, conn, parse_dates=["date"])
    return df


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
        title="SokoData API",
        description=(
            "Open market-price intelligence for African food markets. "
            "Data: World Food Programme Price Database via HDX (CC BY-IGO)."
        ),
        version=__version__,
        lifespan=lifespan,
    )

    @app.get("/", include_in_schema=False)
    def root():
        """Land on the interactive docs instead of a 404."""
        return RedirectResponse(url="/docs")

    @app.get("/health", response_model=None, tags=["meta"])
    def health():
        from sokodata.api.schemas import Health

        return Health(
            status="ok" if app.state.prices is not None else "empty",
            version=__version__,
            coverage=seasonal.coverage(app.state.prices),
            data_credit=DATA_CREDIT,
        )

    app.include_router(markets.router, prefix="/v1")
    app.include_router(commodities.router, prefix="/v1")
    app.include_router(prices.router, prefix="/v1")
    app.include_router(insights.router, prefix="/v1")
    app.include_router(webhooks.router)
    return app


app = create_app()


def serve() -> None:
    uvicorn.run("sokodata.api.main:app", host="0.0.0.0", port=8000, reload=False)


if __name__ == "__main__":
    serve()
