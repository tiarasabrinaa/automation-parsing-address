from __future__ import annotations

from pathlib import Path

import pandas as pd


def save_results(df, output_dir, base_name="parsed_addresses"):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path = output_dir / f"{base_name}.csv"
    xlsx_path = output_dir / f"{base_name}.xlsx"

    df.to_csv(csv_path, index=False)
    df.to_excel(xlsx_path, index=False)

    return {
        "csv": csv_path,
        "xlsx": xlsx_path,
    }
