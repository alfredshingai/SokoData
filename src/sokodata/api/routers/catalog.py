"""Dataset catalog for the SokoData commons."""

from fastapi import APIRouter

from sokodata.core.registry import list_datasets

router = APIRouter(tags=["catalog"])


@router.get("/catalog")
def catalog():
    """List all datasets in the commons with metadata and provenance."""
    return [
        {
            "id": d.id,
            "label": d.label,
            "description": d.description,
            "sources": d.sources,
            "tables": d.tables,
            "update_frequency": d.update_frequency,
            "coverage": d.coverage,
            "fetch_strategy": d.fetch_strategy,
            "status": d.status,
            "tags": d.tags,
        }
        for d in list_datasets()
    ]


@router.get("/catalog/{dataset_id}")
def catalog_one(dataset_id: str):
    from fastapi import HTTPException

    from sokodata.core.registry import get_dataset

    ds = get_dataset(dataset_id)
    if ds is None:
        raise HTTPException(status_code=404, detail=f"dataset {dataset_id} not found")
    return {
        "id": ds.id,
        "label": ds.label,
        "description": ds.description,
        "sources": ds.sources,
        "tables": ds.tables,
        "update_frequency": ds.update_frequency,
        "coverage": ds.coverage,
        "fetch_strategy": ds.fetch_strategy,
        "status": ds.status,
        "tags": ds.tags,
    }
