"""Central configuration: data sources, default paths, country support."""

import os
from pathlib import Path

HDX_DATASET = "https://data.humdata.org/dataset/wfp-food-prices-for-zimbabwe"

# Default country (Zimbabwe)
DEFAULT_COUNTRY = "ZW"

# ISO3 country codes supported (WFP food prices via HDX)
# Resource IDs need to be verified per country on HDX
COUNTRIES = {
    "DZ": {
        "name": "Algeria",
        "iso3": "DZA",
        "hdx_dataset": "wfp-food-prices-for-algeria",
        "prices_url": "https://data.humdata.org/dataset/6ca04cee-665a-4037-b04e-b94a8b2cdef9/resource/ede2e94c-5550-45c8-aac1-5267d65b04c7/download/wfp_food_prices_dza.csv",
        "markets_url": "https://data.humdata.org/dataset/6ca04cee-665a-4037-b04e-b94a8b2cdef9/resource/92757033-242d-4693-aacc-367f7adba25f/download/wfp_markets_dza.csv",
        "wb_country": "DZ",
    },
    "AO": {
        "name": "Angola",
        "iso3": "AGO",
        "hdx_dataset": "wfp-food-prices-for-angola",
        "prices_url": "https://data.humdata.org/dataset/f6155f17-bded-468c-b926-b9de5034d2ad/resource/8d87dc41-26b9-4928-86ec-75f95480e18d/download/wfp_food_prices_ago.csv",
        "markets_url": "https://data.humdata.org/dataset/f6155f17-bded-468c-b926-b9de5034d2ad/resource/db4ce57b-a968-4347-bbed-5ec7d0bf31fe/download/wfp_markets_ago.csv",
        "wb_country": "AO",
    },
    "BJ": {
        "name": "Benin",
        "iso3": "BEN",
        "hdx_dataset": "wfp-food-prices-for-benin",
        "prices_url": "https://data.humdata.org/dataset/66c7d54e-0c3b-45e5-9a46-07ea6f195093/resource/7da1ea0a-56c7-450a-af2c-d477745fc856/download/wfp_food_prices_ben.csv",
        "markets_url": "https://data.humdata.org/dataset/66c7d54e-0c3b-45e5-9a46-07ea6f195093/resource/030d5114-a642-4b5b-8915-019c6f1e8d4e/download/wfp_markets_ben.csv",
        "wb_country": "BJ",
    },
    "BF": {
        "name": "Burkina Faso",
        "iso3": "BFA",
        "hdx_dataset": "wfp-food-prices-for-burkina-faso",
        "prices_url": "https://data.humdata.org/dataset/bfd82e1f-0296-48a8-ac28-c11e028be5ed/resource/0eca67d6-e297-4f5e-9132-7dc42891b749/download/wfp_food_prices_bfa.csv",
        "markets_url": "https://data.humdata.org/dataset/bfd82e1f-0296-48a8-ac28-c11e028be5ed/resource/1a7c613a-acf6-4c8d-a8ce-af5fdec82d13/download/wfp_markets_bfa.csv",
        "wb_country": "BF",
    },
    "BI": {
        "name": "Burundi",
        "iso3": "BDI",
        "hdx_dataset": "wfp-food-prices-for-burundi",
        "prices_url": "https://data.humdata.org/dataset/e7e5df38-adb6-4843-a053-24e119b27afc/resource/efa227dd-2fd5-437e-b79d-130af02b769d/download/wfp_food_prices_bdi.csv",
        "markets_url": "https://data.humdata.org/dataset/e7e5df38-adb6-4843-a053-24e119b27afc/resource/d9a7fb18-bc9b-4a80-8c22-cd1a48a3ca7c/download/wfp_markets_bdi.csv",
        "wb_country": "BI",
    },
    "CV": {
        "name": "Cabo Verde",
        "iso3": "CPV",
        "hdx_dataset": "wfp-food-prices-for-cabo-verde",
        "prices_url": "https://data.humdata.org/dataset/f9f8ff96-61eb-472e-9ec8-814980cfabcd/resource/0894fd0b-53b3-41f5-8897-17c05bc003c7/download/wfp_food_prices_cpv.csv",
        "markets_url": "https://data.humdata.org/dataset/f9f8ff96-61eb-472e-9ec8-814980cfabcd/resource/f99c7f4b-da7e-4df9-90a5-04dda4015658/download/wfp_markets_cpv.csv",
        "wb_country": "CV",
    },
    "CM": {
        "name": "Cameroon",
        "iso3": "CMR",
        "hdx_dataset": "wfp-food-prices-for-cameroon",
        "prices_url": "https://data.humdata.org/dataset/f6ed9f06-36b9-43b2-97f3-fc0b8e16d155/resource/9deec824-1e42-4a91-b704-b73fd250ec5a/download/wfp_food_prices_cmr.csv",
        "markets_url": "https://data.humdata.org/dataset/f6ed9f06-36b9-43b2-97f3-fc0b8e16d155/resource/8aa2efc4-cf2f-4ec2-96af-279fa6f9a7e4/download/wfp_markets_cmr.csv",
        "wb_country": "CM",
    },
    "CF": {
        "name": "Central African Republic",
        "iso3": "CAF",
        "hdx_dataset": "wfp-food-prices-for-central-african-republic",
        "prices_url": "https://data.humdata.org/dataset/e9f27b34-f511-498c-a7f8-fe8d2321f7ba/resource/cb558a54-357a-4bcd-9edd-30caf65b1bd7/download/wfp_food_prices_caf.csv",
        "markets_url": "https://data.humdata.org/dataset/e9f27b34-f511-498c-a7f8-fe8d2321f7ba/resource/ca7cfdb4-a05b-4eee-9c53-c01644ac1aaf/download/wfp_markets_caf.csv",
        "wb_country": "CF",
    },
    "TD": {
        "name": "Chad",
        "iso3": "TCD",
        "hdx_dataset": "wfp-food-prices-for-chad",
        "prices_url": "https://data.humdata.org/dataset/a4f14321-0133-445c-bca4-60a113489fc0/resource/75fbc47f-6c80-4f80-9725-faba737befd1/download/wfp_food_prices_tcd.csv",
        "markets_url": "https://data.humdata.org/dataset/a4f14321-0133-445c-bca4-60a113489fc0/resource/66df120f-7c05-40e1-99b6-c72f837870ce/download/wfp_markets_tcd.csv",
        "wb_country": "TD",
    },
    "CG": {
        "name": "Congo",
        "iso3": "COG",
        "hdx_dataset": "wfp-food-prices-for-congo",
        "prices_url": "https://data.humdata.org/dataset/86dfc591-9de6-44f8-b908-ebba34a96ddf/resource/21bf778a-2cdd-4ca2-b017-9779534d3281/download/wfp_food_prices_cog.csv",
        "markets_url": "https://data.humdata.org/dataset/86dfc591-9de6-44f8-b908-ebba34a96ddf/resource/b90b71e3-b642-446c-a3d8-82e5951280fc/download/wfp_markets_cog.csv",
        "wb_country": "CG",
    },
    "CI": {
        "name": "Cote d'Ivoire",
        "iso3": "CIV",
        "hdx_dataset": "wfp-food-prices-for-cote-d-ivoire",
        "prices_url": "https://data.humdata.org/dataset/e6ff12e6-0670-4a0e-af9f-3750688e6c8d/resource/b54849f9-d90f-48cb-b818-8ea5b60306d5/download/wfp_food_prices_civ.csv",
        "markets_url": "https://data.humdata.org/dataset/e6ff12e6-0670-4a0e-af9f-3750688e6c8d/resource/e2dc7c91-0932-4da9-a14e-32b2bea0aebf/download/wfp_markets_civ.csv",
        "wb_country": "CI",
    },
    "CD": {
        "name": "DR Congo",
        "iso3": "COD",
        "hdx_dataset": "wfp-food-prices-for-democratic-republic-of-the-congo",
        "prices_url": "https://data.humdata.org/dataset/07a6d6fb-828d-4391-afb8-78b1fc32caa3/resource/c9906fd4-9947-450a-b816-682907463f2a/download/wfp_food_prices_cod.csv",
        "markets_url": "https://data.humdata.org/dataset/07a6d6fb-828d-4391-afb8-78b1fc32caa3/resource/a8b7d1d8-701d-467a-98d1-95b402d4d0e4/download/wfp_markets_cod.csv",
        "wb_country": "CD",
    },
    "DJ": {
        "name": "Djibouti",
        "iso3": "DJI",
        "hdx_dataset": "wfp-food-prices-for-djibouti",
        "prices_url": "https://data.humdata.org/dataset/b9e4ffde-205c-4887-beb0-a1fa027e8bdc/resource/1e404d41-2300-4d0b-ba1c-730f55cb58aa/download/wfp_food_prices_dji.csv",
        "markets_url": "https://data.humdata.org/dataset/b9e4ffde-205c-4887-beb0-a1fa027e8bdc/resource/01684b58-f16b-46b9-ae94-d037a92a1d68/download/wfp_markets_dji.csv",
        "wb_country": "DJ",
    },
    "EG": {
        "name": "Egypt",
        "iso3": "EGY",
        "hdx_dataset": "wfp-food-prices-for-egypt",
        "prices_url": "https://data.humdata.org/dataset/230e991f-3438-4763-8044-e424b5a67bec/resource/561cea27-29af-40b8-bf3f-633c734cecb2/download/wfp_food_prices_egy.csv",
        "markets_url": "https://data.humdata.org/dataset/230e991f-3438-4763-8044-e424b5a67bec/resource/e20b5388-eced-4999-875c-a30886fa8428/download/wfp_markets_egy.csv",
        "wb_country": "EG",
    },
    "ER": {
        "name": "Eritrea",
        "iso3": "ERI",
        "hdx_dataset": "wfp-food-prices-for-eritrea",
        "prices_url": "https://data.humdata.org/dataset/4702c45e-cd9e-4e85-aab3-ef506a946a10/resource/075cdb63-d84f-43b8-9dc6-603aeea184b3/download/wfp_food_prices_eri.csv",
        "markets_url": "https://data.humdata.org/dataset/4702c45e-cd9e-4e85-aab3-ef506a946a10/resource/9b4230a2-2032-493d-96ad-0ee9f7aa46b2/download/wfp_markets_eri.csv",
        "wb_country": "ER",
    },
    "SZ": {
        "name": "Eswatini",
        "iso3": "SWZ",
        "hdx_dataset": "wfp-food-prices-for-eswatini",
        "prices_url": "https://data.humdata.org/dataset/da611749-4214-4945-bd97-7f97ffa9ac62/resource/0cf0dfcf-f024-490a-8cf2-582bc06778ec/download/wfp_food_prices_swz.csv",
        "markets_url": "https://data.humdata.org/dataset/da611749-4214-4945-bd97-7f97ffa9ac62/resource/75483c29-8f44-475a-94b2-8e1c8cf3390d/download/wfp_markets_swz.csv",
        "wb_country": "SZ",
    },
    "ET": {
        "name": "Ethiopia",
        "iso3": "ETH",
        "hdx_dataset": "wfp-food-prices-for-ethiopia",
        "prices_url": "https://data.humdata.org/dataset/2e4f1922-e446-4b57-a98a-d0e2d5e34afa/resource/87bac18e-f3aa-4b29-8cf8-76763e823dc5/download/wfp_food_prices_eth.csv",
        "markets_url": "https://data.humdata.org/dataset/2e4f1922-e446-4b57-a98a-d0e2d5e34afa/resource/ffa5efea-691a-46ea-b8d0-7e3f25eb56c8/download/wfp_markets_eth.csv",
        "wb_country": "ET",
    },
    "GA": {
        "name": "Gabon",
        "iso3": "GAB",
        "hdx_dataset": "wfp-food-prices-for-gabon",
        "prices_url": "https://data.humdata.org/dataset/423e0a51-bb5f-4ce8-b269-f0d9319cd8a5/resource/1a1dc63e-448f-4ce7-a409-9d3bb923b0f8/download/wfp_food_prices_gab.csv",
        "markets_url": "https://data.humdata.org/dataset/423e0a51-bb5f-4ce8-b269-f0d9319cd8a5/resource/56751852-88c7-49e7-bb30-cb2f1a09981a/download/wfp_markets_gab.csv",
        "wb_country": "GA",
    },
    "GM": {
        "name": "Gambia",
        "iso3": "GMB",
        "hdx_dataset": "wfp-food-prices-for-gambia",
        "prices_url": "https://data.humdata.org/dataset/ff621ab5-41f7-4caf-8bfa-b9becbe6d934/resource/943c8f83-2df2-47fa-be96-1ac30f28a225/download/wfp_food_prices_gmb.csv",
        "markets_url": "https://data.humdata.org/dataset/ff621ab5-41f7-4caf-8bfa-b9becbe6d934/resource/61e56a3f-624a-478c-a121-575343989f45/download/wfp_markets_gmb.csv",
        "wb_country": "GM",
    },
    "GH": {
        "name": "Ghana",
        "iso3": "GHA",
        "hdx_dataset": "wfp-food-prices-for-ghana",
        "prices_url": "https://data.humdata.org/dataset/626e809c-c4fc-467b-a60c-129acb5e9320/resource/e877350b-146f-4fa7-8690-db9605eea78c/download/wfp_food_prices_gha.csv",
        "markets_url": "https://data.humdata.org/dataset/626e809c-c4fc-467b-a60c-129acb5e9320/resource/e674838c-87ba-4c7c-afc5-614226842768/download/wfp_markets_gha.csv",
        "wb_country": "GH",
    },
    "GN": {
        "name": "Guinea",
        "iso3": "GIN",
        "hdx_dataset": "wfp-food-prices-for-guinea",
        "prices_url": "https://data.humdata.org/dataset/17a0a124-bedd-427c-a710-0d6e87672891/resource/f8e11cd4-630f-44be-afa0-3e7baa5744ca/download/wfp_food_prices_gin.csv",
        "markets_url": "https://data.humdata.org/dataset/17a0a124-bedd-427c-a710-0d6e87672891/resource/a1247273-34cf-4def-9622-f5579d923fbd/download/wfp_markets_gin.csv",
        "wb_country": "GN",
    },
    "GW": {
        "name": "Guinea-Bissau",
        "iso3": "GNB",
        "hdx_dataset": "wfp-food-prices-for-guinea-bissau",
        "prices_url": "https://data.humdata.org/dataset/44bdf939-420d-4a81-9375-81d02a4a9fa2/resource/7da0af7e-1261-43fe-8cae-aecefef288f9/download/wfp_food_prices_gnb.csv",
        "markets_url": "https://data.humdata.org/dataset/44bdf939-420d-4a81-9375-81d02a4a9fa2/resource/6777edd4-78fc-4200-ac1b-4f53d457ac6f/download/wfp_markets_gnb.csv",
        "wb_country": "GW",
    },
    "KE": {
        "name": "Kenya",
        "iso3": "KEN",
        "hdx_dataset": "wfp-food-prices-for-kenya",
        "prices_url": "https://data.humdata.org/dataset/e0d3fba6-f9a2-45d7-b949-140c455197ff/resource/517ee1bf-2437-4f8c-aa1b-cb9925b9d437/download/wfp_food_prices_ken.csv",
        "markets_url": "https://data.humdata.org/dataset/e0d3fba6-f9a2-45d7-b949-140c455197ff/resource/fde6f6c7-9776-4b52-a826-d77f9d3f6688/download/wfp_markets_ken.csv",
        "wb_country": "KE",
    },
    "LS": {
        "name": "Lesotho",
        "iso3": "LSO",
        "hdx_dataset": "wfp-food-prices-for-lesotho",
        "prices_url": "https://data.humdata.org/dataset/e6734ad4-45fa-4db2-a9c0-52eff69f5a08/resource/a32cc3c1-9892-4897-bdc1-f14505a31e8e/download/wfp_food_prices_lso.csv",
        "markets_url": "https://data.humdata.org/dataset/e6734ad4-45fa-4db2-a9c0-52eff69f5a08/resource/fdabd1c9-2c60-4ea6-83e3-49c1d00083b5/download/wfp_markets_lso.csv",
        "wb_country": "LS",
    },
    "LR": {
        "name": "Liberia",
        "iso3": "LBR",
        "hdx_dataset": "wfp-food-prices-for-liberia",
        "prices_url": "https://data.humdata.org/dataset/d21bbefd-fdf0-49e9-aa7c-533c32edabf6/resource/85a224fb-5917-43c8-87f7-d14eca7da1e2/download/wfp_food_prices_lbr.csv",
        "markets_url": "https://data.humdata.org/dataset/d21bbefd-fdf0-49e9-aa7c-533c32edabf6/resource/6018a1f3-bdeb-4a7b-846b-ac448022c2f9/download/wfp_markets_lbr.csv",
        "wb_country": "LR",
    },
    "LY": {
        "name": "Libya",
        "iso3": "LBY",
        "hdx_dataset": "wfp-food-prices-for-libya",
        "prices_url": "https://data.humdata.org/dataset/dc632a15-d376-496f-976f-c3282e67bc28/resource/49e3a2ae-629e-46f3-8529-7e1fd0277b24/download/wfp_food_prices_lby.csv",
        "markets_url": "https://data.humdata.org/dataset/dc632a15-d376-496f-976f-c3282e67bc28/resource/b5817cb1-090e-49ae-b1f6-756b5f38f3df/download/wfp_markets_lby.csv",
        "wb_country": "LY",
    },
    "MG": {
        "name": "Madagascar",
        "iso3": "MDG",
        "hdx_dataset": "wfp-food-prices-for-madagascar",
        "prices_url": "https://data.humdata.org/dataset/86173d84-f1b5-4470-afb9-5ee56747f4cd/resource/8fc13d1e-abac-4262-8caa-edab795661e6/download/wfp_food_prices_mdg.csv",
        "markets_url": "https://data.humdata.org/dataset/86173d84-f1b5-4470-afb9-5ee56747f4cd/resource/f41cbae8-e250-48a6-8584-b822c9a312e7/download/wfp_markets_mdg.csv",
        "wb_country": "MG",
    },
    "MW": {
        "name": "Malawi",
        "iso3": "MWI",
        "hdx_dataset": "wfp-food-prices-for-malawi",
        "prices_url": "https://data.humdata.org/dataset/75ecb747-717e-4ce5-b7af-0e13cc95ba63/resource/da3ed5da-d6ad-4a86-b4bc-b77e74d01ab7/download/wfp_food_prices_mwi.csv",
        "markets_url": "https://data.humdata.org/dataset/75ecb747-717e-4ce5-b7af-0e13cc95ba63/resource/aaf5c1ca-361e-4aa0-8dc6-b8646aaefe67/download/wfp_markets_mwi.csv",
        "wb_country": "MW",
    },
    "ML": {
        "name": "Mali",
        "iso3": "MLI",
        "hdx_dataset": "wfp-food-prices-for-mali",
        "prices_url": "https://data.humdata.org/dataset/d73f8595-0b0b-4b64-91b3-986b1cad5ae6/resource/e7489e71-2c7b-48d4-8ae7-f378b735dcba/download/wfp_food_prices_mli.csv",
        "markets_url": "https://data.humdata.org/dataset/d73f8595-0b0b-4b64-91b3-986b1cad5ae6/resource/746631e3-effe-413d-b996-5dccf6f3deb2/download/wfp_markets_mli.csv",
        "wb_country": "ML",
    },
    "MR": {
        "name": "Mauritania",
        "iso3": "MRT",
        "hdx_dataset": "wfp-food-prices-for-mauritania",
        "prices_url": "https://data.humdata.org/dataset/a17cd464-d4e6-48d0-8bec-e6d3d2f5068a/resource/2c473576-bb75-48b5-b2b0-83ed914bb540/download/wfp_food_prices_mrt.csv",
        "markets_url": "https://data.humdata.org/dataset/a17cd464-d4e6-48d0-8bec-e6d3d2f5068a/resource/e23e8e78-4227-4f96-a81b-5728d002dc6a/download/wfp_markets_mrt.csv",
        "wb_country": "MR",
    },
    "MZ": {
        "name": "Mozambique",
        "iso3": "MOZ",
        "hdx_dataset": "wfp-food-prices-for-mozambique",
        "prices_url": "https://data.humdata.org/dataset/477a46ed-4c31-42e4-b591-a598f7ab5fe6/resource/e673f685-0ea4-440d-afee-76c0f1293fc0/download/wfp_food_prices_moz.csv",
        "markets_url": "https://data.humdata.org/dataset/477a46ed-4c31-42e4-b591-a598f7ab5fe6/resource/95a181b3-6060-4d54-a2bc-d82de8a99f1c/download/wfp_markets_moz.csv",
        "wb_country": "MZ",
    },
    "NA": {
        "name": "Namibia",
        "iso3": "NAM",
        "hdx_dataset": "wfp-food-prices-for-namibia",
        "prices_url": "https://data.humdata.org/dataset/619b52cf-1b1a-48cc-845b-ef073e6ddf80/resource/a0908fa9-c466-4fbb-aad9-569c1ea1e0d8/download/wfp_food_prices_nam.csv",
        "markets_url": "https://data.humdata.org/dataset/619b52cf-1b1a-48cc-845b-ef073e6ddf80/resource/7983fe8d-bb66-439e-9fb9-829301e63d5a/download/wfp_markets_nam.csv",
        "wb_country": "NA",
    },
    "NE": {
        "name": "Niger",
        "iso3": "NER",
        "hdx_dataset": "wfp-food-prices-for-niger",
        "prices_url": "https://data.humdata.org/dataset/9c2f8da3-c0a5-476d-9035-b9b59172b922/resource/87334563-5dae-4125-9bcc-e9418283a8c9/download/wfp_food_prices_ner.csv",
        "markets_url": "https://data.humdata.org/dataset/9c2f8da3-c0a5-476d-9035-b9b59172b922/resource/f90a266d-f9cb-43e2-8c75-638023e44a92/download/wfp_markets_ner.csv",
        "wb_country": "NE",
    },
    "NG": {
        "name": "Nigeria",
        "iso3": "NGA",
        "hdx_dataset": "wfp-food-prices-for-nigeria",
        "prices_url": "https://data.humdata.org/dataset/42db041f-7aaf-4ab4-961f-2a12096861e7/resource/12b51155-0cd3-4806-9924-61ede4077591/download/wfp_food_prices_nga.csv",
        "markets_url": "https://data.humdata.org/dataset/42db041f-7aaf-4ab4-961f-2a12096861e7/resource/5329e772-0b74-4f65-8cc0-37a0915cc7e4/download/wfp_markets_nga.csv",
        "wb_country": "NG",
    },
    "RW": {
        "name": "Rwanda",
        "iso3": "RWA",
        "hdx_dataset": "wfp-food-prices-for-rwanda",
        "prices_url": "https://data.humdata.org/dataset/a4a84c1c-81d1-491b-9fbe-1955ae736508/resource/8c22eeb5-cc2e-46bc-8a0d-08b7486b2486/download/wfp_food_prices_rwa.csv",
        "markets_url": "https://data.humdata.org/dataset/a4a84c1c-81d1-491b-9fbe-1955ae736508/resource/31d038ef-416e-4c66-906f-54de20794918/download/wfp_markets_rwa.csv",
        "wb_country": "RW",
    },
    "SN": {
        "name": "Senegal",
        "iso3": "SEN",
        "hdx_dataset": "wfp-food-prices-for-senegal",
        "prices_url": "https://data.humdata.org/dataset/77b76bc7-1edd-43f6-a5e4-784498ff6aca/resource/04ffc070-6d05-4653-a9f6-9f3f893a229e/download/wfp_food_prices_sen.csv",
        "markets_url": "https://data.humdata.org/dataset/77b76bc7-1edd-43f6-a5e4-784498ff6aca/resource/48a1e809-2a74-4952-8e35-b67f7f1552e2/download/wfp_markets_sen.csv",
        "wb_country": "SN",
    },
    "SL": {
        "name": "Sierra Leone",
        "iso3": "SLE",
        "hdx_dataset": "wfp-food-prices-for-sierra-leone",
        "prices_url": "https://data.humdata.org/dataset/93388727-fdb4-4eb7-8775-9b5b30ae78fa/resource/9249a9f4-6e27-4d52-8603-df302ef862eb/download/wfp_food_prices_sle.csv",
        "markets_url": "https://data.humdata.org/dataset/93388727-fdb4-4eb7-8775-9b5b30ae78fa/resource/36db469d-e158-4c7f-b6b7-fbe6f4804d2a/download/wfp_markets_sle.csv",
        "wb_country": "SL",
    },
    "SO": {
        "name": "Somalia",
        "iso3": "SOM",
        "hdx_dataset": "wfp-food-prices-for-somalia",
        "prices_url": "https://data.humdata.org/dataset/26727d1b-af49-4323-9215-c2ac479abb87/resource/39614bfb-0f9c-4800-8997-e68e41a38ced/download/wfp_food_prices_som.csv",
        "markets_url": "https://data.humdata.org/dataset/26727d1b-af49-4323-9215-c2ac479abb87/resource/bf3725e2-cbb5-4dc2-8d6a-2f2f1c6ef855/download/wfp_markets_som.csv",
        "wb_country": "SO",
    },
    "SS": {
        "name": "South Sudan",
        "iso3": "SSD",
        "hdx_dataset": "wfp-food-prices-for-south-sudan",
        "prices_url": "https://data.humdata.org/dataset/4f48c45b-1a20-4478-b62d-bf637b8d4666/resource/5a3e103d-f352-41f6-94e9-acaad13c66a5/download/wfp_food_prices_ssd.csv",
        "markets_url": "https://data.humdata.org/dataset/4f48c45b-1a20-4478-b62d-bf637b8d4666/resource/73640d00-adb7-4f9f-a5e0-9f8c7f143d9c/download/wfp_markets_ssd.csv",
        "wb_country": "SS",
    },
    "SD": {
        "name": "Sudan",
        "iso3": "SDN",
        "hdx_dataset": "wfp-food-prices-for-sudan",
        "prices_url": "https://data.humdata.org/dataset/369e003b-f0af-4e48-99d7-34fc85b44635/resource/8fea18b2-615f-4af5-9bd5-85cc31a25ffd/download/wfp_food_prices_sdn.csv",
        "markets_url": "https://data.humdata.org/dataset/369e003b-f0af-4e48-99d7-34fc85b44635/resource/6bc993a6-0c4b-47bc-b757-af220aa5f00f/download/wfp_markets_sdn.csv",
        "wb_country": "SD",
    },
    "TZ": {
        "name": "Tanzania",
        "iso3": "TZA",
        "hdx_dataset": "wfp-food-prices-for-united-republic-of-tanzania",
        "prices_url": "https://data.humdata.org/dataset/5090d858-a300-49fe-a953-4ec4e3526fc2/resource/2ff38c1a-a8f7-45b2-9209-090200c859da/download/wfp_food_prices_tza.csv",
        "markets_url": "https://data.humdata.org/dataset/5090d858-a300-49fe-a953-4ec4e3526fc2/resource/12a46292-fef2-412e-9c19-0420028eff0d/download/wfp_markets_tza.csv",
        "wb_country": "TZ",
    },
    "TG": {
        "name": "Togo",
        "iso3": "TGO",
        "hdx_dataset": "wfp-food-prices-for-togo",
        "prices_url": "https://data.humdata.org/dataset/f6b47ff7-48aa-4e13-b2e7-e5e487d43c19/resource/13b52287-f019-49a3-aa56-1480f2aab026/download/wfp_food_prices_tgo.csv",
        "markets_url": "https://data.humdata.org/dataset/f6b47ff7-48aa-4e13-b2e7-e5e487d43c19/resource/2da294f6-878e-4111-8644-1bd7ef5834b6/download/wfp_markets_tgo.csv",
        "wb_country": "TG",
    },
    "UG": {
        "name": "Uganda",
        "iso3": "UGA",
        "hdx_dataset": "wfp-food-prices-for-uganda",
        "prices_url": "https://data.humdata.org/dataset/883929b1-521e-4834-97f5-0ccc2df75b89/resource/e082d683-cad5-4dcd-bf54-db76ae254d33/download/wfp_food_prices_uga.csv",
        "markets_url": "https://data.humdata.org/dataset/883929b1-521e-4834-97f5-0ccc2df75b89/resource/4ef683cd-ccdd-4f96-9dc3-e25e6af88d25/download/wfp_markets_uga.csv",
        "wb_country": "UG",
    },
    "ZM": {
        "name": "Zambia",
        "iso3": "ZMB",
        "hdx_dataset": "wfp-food-prices-for-zambia",
        "prices_url": "https://data.humdata.org/dataset/3f74001c-3554-4c54-bd86-c66208563316/resource/d9a34dc4-ff1d-43bf-9592-03d12d027848/download/wfp_food_prices_zmb.csv",
        "markets_url": "https://data.humdata.org/dataset/3f74001c-3554-4c54-bd86-c66208563316/resource/d1e180e1-75b2-41e4-9794-9d5f15e6672c/download/wfp_markets_zmb.csv",
        "wb_country": "ZM",
    },
    "ZW": {
        "name": "Zimbabwe",
        "iso3": "ZWE",
        "hdx_dataset": "wfp-food-prices-for-zimbabwe",
        "prices_url": "https://data.humdata.org/dataset/d878cfac-a45f-48bd-8460-a2e16ab0ea94/resource/7c48c192-36d4-422e-996d-19cc62e2e4fd/download/wfp_food_prices_zwe.csv",
        "markets_url": "https://data.humdata.org/dataset/d878cfac-a45f-48bd-8460-a2e16ab0ea94/resource/69d1652a-ee48-42a1-b4a7-1321296c31ac/download/wfp_markets_zwe.csv",
        "wb_country": "ZW",
    },
}


def get_country_config(country: str = DEFAULT_COUNTRY) -> dict:
    """Get configuration for a specific country."""
    # Handle Path objects passed by mistake
    if hasattr(country, "name"):
        country = str(country)
    key = str(country).upper()
    if key not in COUNTRIES:
        raise ValueError(f"Unknown country {country!r}. Configured: {', '.join(sorted(COUNTRIES))}")
    return COUNTRIES[key]


def get_prices_url(country: str = DEFAULT_COUNTRY) -> str:
    """Build WFP prices URL for a country."""
    cfg = get_country_config(country)
    if cfg.get("prices_url"):
        return cfg["prices_url"]
    if cfg["prices_resource"]:
        return (
            f"https://data.humdata.org/dataset/"
            f"{cfg['hdx_dataset']}/resource/"
            f"{cfg['prices_resource']}/download/wfp_food_prices_{cfg['iso3'].lower()}.csv"
        )
    # Fallback: try standard pattern
    return (
        f"https://data.humdata.org/dataset/"
        f"wfp-food-prices-for-{cfg['name'].lower()}/resource/"
        f"download/wfp_food_prices_{cfg['iso3'].lower()}.csv"
    )


def get_markets_url(country: str = DEFAULT_COUNTRY) -> str:
    """Build WFP markets URL for a country."""
    cfg = get_country_config(country)
    if cfg.get("markets_url"):
        return cfg["markets_url"]
    if cfg["markets_resource"]:
        return (
            f"https://data.humdata.org/dataset/"
            f"{cfg['hdx_dataset']}/resource/"
            f"{cfg['markets_resource']}/download/wfp_markets_{cfg['iso3'].lower()}.csv"
        )
    return (
        f"https://data.humdata.org/dataset/"
        f"wfp-food-prices-for-{cfg['name'].lower()}/resource/"
        f"download/wfp_markets_{cfg['iso3'].lower()}.csv"
    )


def get_wb_country(country: str = DEFAULT_COUNTRY) -> str:
    """Get World Bank country code for a country."""
    return get_country_config(country)["wb_country"]


def resolve_iso3(country: str) -> str:
    """Normalize ISO2 (ZW) or ISO3 (ZWE) input to the ISO3 used in the warehouse."""
    code = str(country).strip().upper()
    if len(code) == 2:
        return get_country_config(code)["iso3"]
    return code


# Attribution required by CC BY-IGO; surfaced in /health and the README.
DATA_CREDIT = {
    "source": "World Food Programme Price Database, via HDX (OCHA)",
    "dataset": HDX_DATASET,
    "license": "CC BY-IGO",
}

_DATA_DIR = os.environ.get("SOKODATA_DATA_DIR", "data")
DB_PATH = Path(_DATA_DIR) / "sokodata.db"
RAW_DIR = Path(_DATA_DIR) / "raw"

USER_AGENT = "sokodata-etl/0.1 (+https://github.com/alfredshingai/sokodata)"
REQUEST_TIMEOUT = 60
