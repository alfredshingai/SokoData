"""Commodity reference endpoints."""

from fastapi import APIRouter, Query, Request

from sokodata.api.schemas import Commodity

router = APIRouter(tags=["commodities"])


@router.get("/commodities", response_model=list[Commodity])
def list_commodities(
    request: Request,
    category: str | None = Query(default=None, max_length=40),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
):
    """List commodities with observation and market coverage counts."""
    df = request.app.state.prices
    grouped = (
        df.groupby(["commodity_id", "commodity", "category", "unit"])
        .agg(observations=("commodity_id", "size"), markets=("market_id", "nunique"))
        .reset_index()
        .sort_values("commodity")
    )
    if category:
        cat = category.lower()
        grouped = grouped[grouped["category"].str.lower() == cat]
    grouped = grouped.iloc[offset : offset + limit]
    return [
        {
            "commodity_id": int(r.commodity_id),
            "commodity": r.commodity,
            "category": r.category,
            "unit": r.unit,
            "observations": int(r.observations),
            "markets": int(r.markets),
        }
        for r in grouped.itertuples(index=False)
    ]
