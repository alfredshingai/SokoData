"""Fetch indicators data from World Bank and UN sources.

* World Bank WDI (open JSON, CC BY-4.0) - SDG indicators
* UNSD SDG API - Official SDG indicators
* National Development Plan indicators from stats offices
"""

import logging
from pathlib import Path

import pandas as pd

from sokodata.config import RAW_DIR, get_wb_country
from sokodata.core.fetch import download_pdf, extract_pdf_tables, fetch_html_tables, fetch_json

log = logging.getLogger(__name__)

# World Bank WDI - SDG indicators
WDI_SDG_INDICATORS = {
    "sg_gen_parl_zs": "SG.GEN.PARL.ZS",           # Women in parliament (%)
    "sg_law_131_1": "SG.LAW.131.1",               # Legal frameworks for gender equality
    "sh_sta_mmr": "SH.STA.MMR",                    # Maternal mortality ratio
    "sh_sta_brtc": "SH.STA.BRTC",                  # Birth registration (%)
    "sh_dyn_mort": "SH.DYN.MORT",                  # Under-5 mortality rate
    "sh_sta_stnt": "SH.STA.STNT",                  # Stunting, height for age (%)
    "sh_sta_wast": "SH.STA.WAST",                  # Wasting, weight for height (%)
    "sh_sta_owgh": "SH.STA.OWGH",                  # Overweight, weight for height (%)
    "sh_imm_meas": "SH.IMM.MEAS",                  # Immunization, measles (%)
    "sh_imm_idpt": "SH.IMM.IDPT",                  # Immunization, DPT (%)
    "sh_imm_hepb": "SH.IMM.HEPB",                  # Immunization, HepB3 (%)
    "sh_h2o_smdw": "SH.H2O.SMDW.ZS",               # Safely managed drinking water (%)
    "sh_sta_smsz": "SH.STA.SMSZ",                  # Safely managed sanitation (%)
    "sh_h2o_basw": "SH.H2O.BASW.ZS",               # Basic drinking water (%)
    "sh_sta_bass": "SH.STA.BASS",                  # Basic sanitation (%)
    "eg_elc_accs_zs": "EG.ELC.ACCS.ZS",            # Access to electricity (%)
    "eg_elc_rnw_xz": "EG.ELC.RNWX.ZS",             # Renewable electricity (%)
    "eg_fec_rnew_zs": "EG.FEC.RNEW.ZS",            # Renewable energy consumption (%)
    "se_prm_nenr": "SE.PRM.NENR",                  # Primary net enrollment (%)
    "se_sec_nenr": "SE.SEC.NENR",                  # Secondary net enrollment (%)
    "se_ter_enrr": "SE.TER.ENRR",                  # Tertiary enrollment (%)
    "se_prm_cmpt_zs": "SE.PRM.CMPT.ZS",            # Primary completion rate (%)
    "sl_ue_totl_zs": "SL.UEM.TOTL.ZS",             # Unemployment (%)
    "sl_tlf_cact_zs": "SL.TLF.CACT.ZS",            # Labor force participation (%)
    "sl_emp_vuln_zs": "SL.EMP.VULN.ZS",            # Vulnerable employment (%)
    "si_pov_dday": "SI.POV.DDAY",                  # Extreme poverty (%)
    "si_pov_gini": "SI.POV.GINI",                  # Gini index
    "si_pov_lmic": "SI.POV.LMIC",                  # Poverty headcount at $3.65/day
    "si_pov_umic": "SI.POV.UMIC",                  # Poverty headcount at $6.85/day
    "ny_gdp_pcap_kd": "NY.GDP.PCAP.KD",            # GDP per capita (constant 2015 US$)
    "ny_gdp_mkp_kd_zg": "NY.GDP.MKTP.KD.ZG",       # GDP growth (%)
    "fp_cpi_totl_zg": "FP.CPI.TOTL.ZG",            # Inflation, consumer prices (%)
    "gc_dod_totl_gd_zs": "GC.DOD.TOTL.GD.ZS",      # Central government debt (% GDP)
    "bx_trf_pwkr_dt": "BX.TRF.PWKR.DT",            # Personal remittances received (current US$)
    "dt_oda_alld_cd": "DT.ODA.ALLD.CD",            # Net ODA received (current US$)
    "dt_oda_odat_gn_zs": "DT.ODA.ODAT.GN.ZS",      # Net ODA (% of GNI)
}

UNSD_SDG_API_BASE = "https://unstats.un.org/SDGAPI/v1/sdg/Indicator/List"


def _fetch_wdi_indicator(indicator: str, country: str) -> pd.DataFrame:
    """Fetch a single WDI indicator for a country."""
    wb_country = get_wb_country(country)
    url = f"https://api.worldbank.org/v2/country/{get_wb_country(country)}/indicator/{indicator}?format=json&per_page=1000&date=2000:2030"
    try:
        data = fetch_json(f"https://api.worldbank.org/v2/country/{get_wb_country(country)}/indicator/{indicator}?format=json&per_page=1000&date=2000:2030")
        recs = data[1] if isinstance(data, list) and len(data) > 1 else []
        rows = []
        for r in recs:
            if r.get("value") is None or r.get("date") is None:
                continue
            rows.append({"date": f"{r['date']}-12-31", "value": float(r["value"]), "indicator": indicator, "source": f"WDI {indicator}"})
        df = pd.DataFrame(rows)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
        log.info("WDI %s for %s: %d points", indicator, country, len(df))
        return df
    except Exception as e:
        log.warning("WDI %s for %s failed: %s", indicator, country, e)
        return pd.DataFrame(columns=["date", "value", "indicator", "source"])


def fetch_wdi_sdg(country: str = "ZW") -> pd.DataFrame:
    """Fetch all SDG indicators from World Bank for a country."""
    wb_country = get_wb_country(country)
    dfs = []
    for indicator, col_name in WDI_SDG_INDICATORS.items():
        df = _fetch_wdi_indicator(col_name, country)
        if not df.empty:
            df = df.rename(columns={"value": indicator})
            dfs.append(df)
    
    if not dfs:
        return pd.DataFrame(columns=["date", "country"])
    
    out = dfs[0]
    for df in dfs[1:]:
        out = out.merge(df, on="date", how="outer")
    out = out.sort_values("date").reset_index(drop=True)
    out["country"] = country
    out["source"] = "World Bank WDI SDG"
    return out


def fetch_unsd_sdg(country: str = "ZW") -> pd.DataFrame:
    """Fetch SDG data from UNSD SDG API."""
    try:
        # UNSD SDG API for a specific country
        url = f"https://unstats.un.org/SDGAPI/v1/sdg/Series/Data?series=ALL&area={country}"
        data = fetch_json(url)
        # Parse UNSD format
        rows = []
        for item in data.get("value", []):
            rows.append({
                "date": f"{item.get('TimePeriod', '')}-12-31",
                "indicator": item.get("SeriesCode", ""),
                "value": float(item.get("Value", 0)) if item.get("Value") else None,
                "source": "UNSD SDG"
            })
        df = pd.DataFrame(rows)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            df["country"] = country
        return df
    except Exception as e:
        log.warning("UNSD SDG fetch failed: %s", e)
        return pd.DataFrame()


def fetch_ndp_indicators(country: str = "ZW") -> pd.DataFrame:
    """Fetch National Development Plan indicators from stats office."""
    # Placeholder for country-specific NDP indicators
    # Would scrape stats office or planning commission
    return pd.DataFrame()


def fetch_indicators_all(country: str = "ZW", raw_dir: str | None = None) -> dict[str, pd.DataFrame]:
    """Fetch all indicator sources for a country."""
    wdi = fetch_wdi_sdg(country)
    unsd = fetch_unsd_sdg(country)
    ndp = fetch_ndp_indicators(country)
    
    # Combine WDI and UNSD (both annual)
    annual = wdi
    if not unsd.empty:
        # Merge UNSD data
        pass
    
    return {"annual": wdi, "unsd": unsd, "ndp": ndp}