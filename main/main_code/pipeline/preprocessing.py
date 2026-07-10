from __future__ import annotations

from pathlib import Path

import pandas as pd

from ...utils.database import add_core_name, get_kodepos, get_level, get_wilayah


def preprocessing_database():
    wilayah = get_wilayah()
    kode_pos = get_kodepos()

    wilayah = wilayah.copy()
    wilayah["nama"] = wilayah["nama"].astype(str).str.upper().str.strip()
    wilayah = wilayah.dropna(subset=["kode", "nama"])
    wilayah["level"] = wilayah["kode"].apply(get_level)

    df_prov = wilayah[wilayah["level"] == "provinsi"].reset_index(drop=True)
    df_kabkota = wilayah[wilayah["level"] == "kabkota"].reset_index(drop=True)
    df_kec = wilayah[wilayah["level"] == "kecamatan"].reset_index(drop=True)
    df_desa = wilayah[wilayah["level"] == "desa"].reset_index(drop=True)

    df_prov, df_kabkota, df_kec, df_desa = add_core_name(df_prov, df_kabkota, df_kec, df_desa)

    return df_prov, df_kabkota, df_kec, df_desa, kode_pos


def load_master_addresses(csv_path, limit=50, address_column="Alamat Lengkap"):
    csv_path = Path(csv_path)
    master_df = pd.read_csv(csv_path, usecols=[address_column], nrows=limit)
    master_df = master_df.rename(columns={address_column: "Alamat Lengkap"})
    master_df["alamat_clean"] = master_df["Alamat Lengkap"].astype(str).str.upper().str.strip()
    return master_df
