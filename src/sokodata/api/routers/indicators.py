"""Indicators endpoints."""

from fastapi import APIRouter, Query, Request

router = APIRouter(prefix="/indicators", tags=["indicators"])


@router.get("/annual")
def indicators_annual(
    request: Request,
    country: str | None = Query(default=None, max_length=3, description="Country ISO3 code"),
    indicator: str | None = Query(default=None, description="Specific indicator code"),
    limit: int = Query(default=100, ge=1, le=5000),
    offset: int = Query(default=0, ge=0),
):
    """Get annual SDG/NDP indicators."""
    sql = "SELECT * FROM indicators_annual"
    params = []
    clauses = []
    if country:
        clauses.append("country = ?")
        params.append(country.upper())
    if indicator:
        # Would need to know column name - for now skip
        pass
    sql = "SELECT * FROM indicators_annual"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY date DESC LIMIT ? OFFSET ?"
    params = [limit, offset]
    try:
        rows = request.app.state.conn.execute(sql, params).fetchall()
    except Exception:
        return []
    return [dict(r) for r in rows]


@router.get("/metadata")
def indicators_metadata():
    """Get metadata about available indicators."""
    return {
        "indicators": {
            "sg_gen_parl_zs": "Women in parliament (%)",
            "sh_sta_mmr": "Maternal mortality ratio",
            "sh_sta_brtc": "Birth registration (%)",
            "sh_dyn_mort": "Under-5 mortality rate",
            "sh_sta_stnt": "Stunting prevalence (%)",
            "sh_h2o_smdw": "Safely managed drinking water (%)",
            "sh_sta_smsz": "Safely managed sanitation (%)",
            "eg_elc_accs_zs": "Access to electricity (%)",
            "eg_fec_rnew_zs": "Renewable energy consumption (%)",
            "se_prm_nenr": "Primary net enrollment (%)",
            "se_sec_nenr": "Secondary net enrollment (%)",
            "sl_ue_totl_zs": "Unemployment rate (%)",
            "si_pov_dday": "Extreme poverty rate (%)",
            "si_pov_gini": "Gini index",
            "ny_gdp_pcap_kd": "GDP per capita (constant 2015 US$)",
            "fp_cpi_totl_zg": "Inflation, consumer prices (%)",
            # ... more indicators
        }
    }