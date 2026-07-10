from __future__ import annotations

import os

import pandas as pd
from sqlalchemy import create_engine

ADMIN_WORDS = {"KOTA", "KABUPATEN", "KAB", "ADMINISTRASI", "ADM"}
DEFAULT_DATABASE_URL = os.getenv("WILAYAH_DATABASE_URL", "postgresql://tiarasabrina@localhost:5432/wilayah_db")
_ENGINE = None


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        _ENGINE = create_engine(DEFAULT_DATABASE_URL)
    return _ENGINE


def get_wilayah(db_engine=None):
    query = "SELECT kode, nama FROM wilayah.wilayah"
    return pd.read_sql(query, db_engine or get_engine())


def get_kodepos(db_engine=None):
    query = "SELECT kode, kodepos FROM wilayah_kodepos.wilayah_kodepos"
    return pd.read_sql(query, db_engine or get_engine())


def get_level(kode):
    parts = str(kode).split(".")
    return {1: "provinsi", 2: "kabkota", 3: "kecamatan", 4: "desa"}.get(len(parts), "unknown")


def add_core_name(*dfs):
    def core_name(nama):
        tokens = str(nama).replace(".", " ").split()
        return " ".join(t for t in tokens if t not in ADMIN_WORDS).strip()

    processed = []
    for df in dfs:
        df = df.copy()
        df["nama_core"] = df["nama"].apply(core_name)
        processed.append(df)

    if len(processed) == 1:
        return processed[0]
    return tuple(processed)

def preprocessing_database():
    wilayah = get_wilayah()
    kode_pos = get_kodepos()

    wilayah["nama"] = wilayah["nama"].str.upper().str.strip()
    wilayah = wilayah.dropna(subset=["kode", "nama"])
    wilayah["level"] = wilayah["kode"].apply(get_level)

    df_prov    = wilayah[wilayah["level"] == "provinsi"].reset_index(drop=True)
    df_kabkota = wilayah[wilayah["level"] == "kabkota"].reset_index(drop=True)
    df_kec     = wilayah[wilayah["level"] == "kecamatan"].reset_index(drop=True)
    df_desa    = wilayah[wilayah["level"] == "desa"].reset_index(drop=True)

    df_kabkota = add_core_name(df_kabkota)

    return df_prov, df_kabkota, df_kec, df_desa, kode_pos