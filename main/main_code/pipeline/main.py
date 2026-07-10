from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd
from tqdm.auto import tqdm

if __package__ in {None, ""}:
    project_root = Path(__file__).resolve().parents[3]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from main.main_code.pipeline.preprocessing import load_master_addresses, preprocessing_database
    from main.main_code.results.results import save_results
    from main.utils.area_extraction import match_wilayah_final
    from main.utils.detail_extraction import extract_address_parts, get_known_wilayah_tokens
else:
    from .preprocessing import load_master_addresses, preprocessing_database
    from ..results.results import save_results
    from ...utils.area_extraction import match_wilayah_final
    from ...utils.detail_extraction import extract_address_parts, get_known_wilayah_tokens


DEFAULT_INPUT_PATH = Path(
    "/Users/tiarasabrina/Documents/PROJECT/AI/address-parsing/master-data/master-matched/Master_Matching_20260701_1059 (1)_matched.csv"
)
DEFAULT_OUTPUT_DIR = Path("/Users/tiarasabrina/Documents/PROJECT/AI/address-parsing/master-data/master-matched")


def build_parser():
    parser = argparse.ArgumentParser(description="Parse Indonesian addresses into structured fields.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT_PATH), help="Path to master-matched CSV input.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Directory used to save parsed results.")
    parser.add_argument("--limit", type=int, default=50, help="Number of rows to parse from the input file.")
    return parser


def parse_one_address(address, kodepos_df, df_prov, df_kabkota, df_kec, df_desa, known_wilayah_tokens):
    raw_text = "" if pd.isna(address) else str(address)
    alamat_clean = " ".join(raw_text.upper().split())

    parts = extract_address_parts(alamat_clean, known_wilayah_tokens=known_wilayah_tokens)
    wilayah_result = match_wilayah_final(
        parts["remaining_text"],
        kodepos=parts["kodepos"],
        kodepos_df=kodepos_df,
        df_prov=df_prov,
        df_kabkota=df_kabkota,
        df_kec=df_kec,
        df_desa=df_desa,
    )

    return {
        "alamat_raw": raw_text,
        **parts,
        **wilayah_result,
    }


def parse_addresses(df, kodepos_df, df_prov, df_kabkota, df_kec, df_desa):
    known_wilayah_tokens = get_known_wilayah_tokens(df_prov, df_kabkota, df_kec, df_desa)

    parsed_rows = []
    for row in tqdm(df.itertuples(index=False), total=len(df), desc="Parsing addresses"):
        parsed_rows.append(
            parse_one_address(
                getattr(row, "Alamat_Lengkap"),
                kodepos_df,
                df_prov,
                df_kabkota,
                df_kec,
                df_desa,
                known_wilayah_tokens,
            )
        )

    parsed_df = pd.concat([df.reset_index(drop=True), pd.DataFrame(parsed_rows)], axis=1)
    return parsed_df


def main(input_path=DEFAULT_INPUT_PATH, output_dir=DEFAULT_OUTPUT_DIR, limit=50):
    df_prov, df_kabkota, df_kec, df_desa, kodepos_df = preprocessing_database()
    master_df = load_master_addresses(input_path, limit=limit)

    parsed_df = parse_addresses(master_df, kodepos_df, df_prov, df_kabkota, df_kec, df_desa)
    outputs = save_results(parsed_df, output_dir, base_name=f"parsed_master_{limit}")

    print(f"Parsed {len(parsed_df)} rows")
    print(f"Saved CSV: {outputs['csv']}")
    print(f"Saved Excel: {outputs['xlsx']}")

    return parsed_df, outputs


if __name__ == "__main__":
    args = build_parser().parse_args()
    main(args.input, args.output_dir, args.limit)
