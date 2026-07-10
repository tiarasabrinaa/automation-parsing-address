from __future__ import annotations

import logging
import re

import pandas as pd
from rapidfuzz import fuzz, process

from .base import expand_abbreviations, tokenize

GENERIC_PREFIXES = {"KABUPATEN", "KAB", "KOTA", "KECAMATAN", "KEC", "DESA", "KELURAHAN", "KEL"}
STRICT_THRESHOLD = 98


def sequence_in_tokens(cand_tokens, text_tokens):
    n, m = len(cand_tokens), len(text_tokens)
    if n == 0 or n > m:
        return False
    for i in range(m - n + 1):
        if text_tokens[i : i + n] == cand_tokens:
            return True
    return False


def exact_match_safe(text_tokens, candidates_df, min_len=4, name_col="nama_core"):
    if candidates_df.empty:
        return None, None

    if name_col not in candidates_df.columns:
        candidates_df = candidates_df.copy()
        candidates_df[name_col] = candidates_df["nama"].astype(str)

    text_tokens_set = set(text_tokens)
    cand_sorted = candidates_df.assign(_len=candidates_df[name_col].astype(str).str.len()).sort_values("_len", ascending=False)
    for _, row in cand_sorted.iterrows():
        core = row[name_col]
        if not core or len(core) < min_len:
            continue
        cand_tokens = tokenize(core)
        if not cand_tokens:
            continue
        if sequence_in_tokens(cand_tokens, text_tokens):
            return row["nama"], row["kode"]
        cand_nospace = "".join(cand_tokens)
        if len(cand_tokens) > 1 and cand_nospace in text_tokens_set and len(cand_nospace) >= min_len:
            return row["nama"], row["kode"]
    return None, None


def fuzzy_match_one(text, candidates_df, score_cutoff=STRICT_THRESHOLD):
    if candidates_df.empty:
        return None, None, 0
    match = process.extractOne(text, candidates_df["nama"], scorer=fuzz.token_set_ratio, score_cutoff=score_cutoff)
    if not match:
        return None, None, 0
    _, score, idx = match
    row = candidates_df.loc[idx]
    if isinstance(row, pd.DataFrame):
        row = row.iloc[0]
    return row["nama"], row["kode"], score


def remove_matched_text(text, matched_name):
    if not matched_name:
        return text

    words = [w for w in re.split(r"\s+", matched_name.strip()) if w and w.upper() not in GENERIC_PREFIXES]
    cleaned = text
    for word in words:
        pattern = r"\b" + re.escape(word) + r"\b"
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", cleaned).strip()


def common_kode_prefix(kode_list):
    splits = [str(k).split(".") for k in kode_list if pd.notna(k)]
    if not splits:
        return []

    max_level = min(len(split) for split in splits)
    common = []
    for i in range(max_level):
        values = {split[i] for split in splits}
        if len(values) == 1:
            common.append(splits[0][i])
        else:
            break
    return common


def find_desa_bigram_match(tokens, desa_pool, min_len=6):
    if desa_pool.empty or len(tokens) < 2:
        return None, None

    names_map = {str(n).strip().upper(): (n, k) for n, k in zip(desa_pool["nama"], desa_pool["kode"])}
    for i in range(len(tokens) - 1):
        joined = (tokens[i] + tokens[i + 1]).upper()
        if len(joined) >= min_len and joined in names_map:
            return names_map[joined]
    return None, None


def match_wilayah_final(leftover_text, kodepos=None, kodepos_df=None, df_prov=None, df_kabkota=None, df_kec=None, df_desa=None):
    leftover_text = (leftover_text or "").strip().upper()

    tokens = tokenize(expand_abbreviations(leftover_text))
    result = {
        "provinsi": None, "kode_prov": None, "score_prov": 0,
        "kabkota": None, "kode_kabkota": None, "score_kabkota": 0,
        "kecamatan": None, "kode_kec": None, "score_kec": 0,
        "desa": None, "kode_desa": None, "score_desa": 0,
        "match_path": None,
    }

    if kodepos:
        kandidat_kode = kodepos_df.loc[kodepos_df["kodepos"] == str(kodepos), "kode"].tolist()
        if kandidat_kode:
            logging.debug("kodepos '%s' -> %s kandidat kode wilayah", kodepos, len(kandidat_kode))
            result["match_path"] = "with_postcode"

            pool_desa = df_desa[df_desa["kode"].isin(kandidat_kode)]
            nama_d, kode_d = exact_match_safe(tokens, pool_desa, min_len=4)
            score_d = 100
            if not nama_d:
                nama_d, kode_d = find_desa_bigram_match(tokens, pool_desa)
                if nama_d:
                    score_d = 100
            if not nama_d:
                nama_d, kode_d, score_d = fuzzy_match_one(leftover_text, pool_desa, score_cutoff=STRICT_THRESHOLD)

            if nama_d:
                parts = kode_d.split(".")
                result["desa"], result["kode_desa"], result["score_desa"] = nama_d, kode_d, score_d
                row_kec = df_kec[df_kec["kode"] == ".".join(parts[:3])]
                row_kab = df_kabkota[df_kabkota["kode"] == ".".join(parts[:2])]
                row_prov = df_prov[df_prov["kode"] == parts[0]]
                if not row_kec.empty:
                    result["kecamatan"], result["kode_kec"], result["score_kec"] = row_kec.iloc[0]["nama"], ".".join(parts[:3]), score_d
                if not row_kab.empty:
                    result["kabkota"], result["kode_kabkota"], result["score_kabkota"] = row_kab.iloc[0]["nama"], ".".join(parts[:2]), score_d
                if not row_prov.empty:
                    result["provinsi"], result["kode_prov"], result["score_prov"] = row_prov.iloc[0]["nama"], parts[0], score_d
            else:
                common = common_kode_prefix(kandidat_kode)
                derived_score = 90

                if len(common) >= 3:
                    kode_kec_common = ".".join(common[:3])
                    row_kec = df_kec[df_kec["kode"] == kode_kec_common]
                    if not row_kec.empty:
                        result["kecamatan"], result["kode_kec"], result["score_kec"] = row_kec.iloc[0]["nama"], kode_kec_common, derived_score
                if len(common) >= 2:
                    kode_kab_common = ".".join(common[:2])
                    row_kab = df_kabkota[df_kabkota["kode"] == kode_kab_common]
                    if not row_kab.empty:
                        result["kabkota"], result["kode_kabkota"], result["score_kabkota"] = row_kab.iloc[0]["nama"], kode_kab_common, derived_score
                if len(common) >= 1:
                    row_prov = df_prov[df_prov["kode"] == common[0]]
                    if not row_prov.empty:
                        result["provinsi"], result["kode_prov"], result["score_prov"] = row_prov.iloc[0]["nama"], common[0], derived_score

            return result

    result["match_path"] = "without_postcode"

    nama_p, kode_p = exact_match_safe(tokens, df_prov, min_len=4)
    score_p = 100
    if not nama_p:
        nama_p, kode_p, score_p = fuzzy_match_one(leftover_text, df_prov, score_cutoff=STRICT_THRESHOLD)
    if nama_p:
        result["provinsi"], result["kode_prov"], result["score_prov"] = nama_p, kode_p, score_p
        leftover_text = remove_matched_text(leftover_text, nama_p)
        tokens = tokenize(expand_abbreviations(leftover_text))

    kandidat_kab = df_kabkota[df_kabkota["kode"].str.startswith(kode_p + ".")] if nama_p else df_kabkota
    nama_k, kode_k = exact_match_safe(tokens, kandidat_kab, min_len=4)
    score_k = 100
    if not nama_k:
        nama_k, kode_k, score_k = fuzzy_match_one(leftover_text, kandidat_kab, score_cutoff=STRICT_THRESHOLD)
    if nama_k:
        result["kabkota"], result["kode_kabkota"], result["score_kabkota"] = nama_k, kode_k, score_k
        if not nama_p:
            kp_derived = kode_k.split(".")[0]
            row_prov = df_prov[df_prov["kode"] == kp_derived]
            if not row_prov.empty:
                result["provinsi"], result["kode_prov"], result["score_prov"] = row_prov.iloc[0]["nama"], kp_derived, score_k
        leftover_text = remove_matched_text(leftover_text, nama_k)
        tokens = tokenize(expand_abbreviations(leftover_text))

    desa_scope = df_desa[df_desa["kode"].str.startswith(kode_k + ".")] if nama_k else df_desa
    bigram_nama_d, bigram_kode_d = find_desa_bigram_match(tokens, desa_scope)
    if bigram_nama_d:
        parts = bigram_kode_d.split(".")
        result["desa"], result["kode_desa"], result["score_desa"] = bigram_nama_d, bigram_kode_d, 100
        row_kec = df_kec[df_kec["kode"] == ".".join(parts[:3])]
        row_kab = df_kabkota[df_kabkota["kode"] == ".".join(parts[:2])]
        row_prov = df_prov[df_prov["kode"] == parts[0]]
        if not row_kec.empty:
            result["kecamatan"], result["kode_kec"], result["score_kec"] = row_kec.iloc[0]["nama"], ".".join(parts[:3]), 100
        if not result["kabkota"] and not row_kab.empty:
            result["kabkota"], result["kode_kabkota"], result["score_kabkota"] = row_kab.iloc[0]["nama"], ".".join(parts[:2]), 100
        if not result["provinsi"] and not row_prov.empty:
            result["provinsi"], result["kode_prov"], result["score_prov"] = row_prov.iloc[0]["nama"], parts[0], 100
        return result

    kandidat_kec = df_kec[df_kec["kode"].str.startswith(kode_k + ".")] if nama_k else df_kec
    nama_c, kode_c = exact_match_safe(tokens, kandidat_kec, min_len=4)
    score_c = 100
    if not nama_c:
        nama_c, kode_c, score_c = fuzzy_match_one(leftover_text, kandidat_kec, score_cutoff=STRICT_THRESHOLD)
    if nama_c:
        result["kecamatan"], result["kode_kec"], result["score_kec"] = nama_c, kode_c, score_c
        if not nama_k:
            kk_derived = ".".join(kode_c.split(".")[:2])
            row_kab = df_kabkota[df_kabkota["kode"] == kk_derived]
            if not row_kab.empty:
                result["kabkota"], result["kode_kabkota"], result["score_kabkota"] = row_kab.iloc[0]["nama"], kk_derived, score_c
            if not result["provinsi"]:
                kp_derived = kode_c.split(".")[0]
                row_prov = df_prov[df_prov["kode"] == kp_derived]
                if not row_prov.empty:
                    result["provinsi"], result["kode_prov"], result["score_prov"] = row_prov.iloc[0]["nama"], kp_derived, score_c
        leftover_text = remove_matched_text(leftover_text, nama_c)
        tokens = tokenize(expand_abbreviations(leftover_text))

    kandidat_desa = df_desa[df_desa["kode"].str.startswith(kode_c + ".")] if nama_c else df_desa
    nama_d, kode_d = exact_match_safe(tokens, kandidat_desa, min_len=4)
    score_d = 100
    if not nama_d:
        nama_d, kode_d = find_desa_bigram_match(tokens, kandidat_desa)
        if nama_d:
            score_d = 100
    if not nama_d:
        nama_d, kode_d, score_d = fuzzy_match_one(leftover_text, kandidat_desa, score_cutoff=STRICT_THRESHOLD)
    if nama_d:
        result["desa"], result["kode_desa"], result["score_desa"] = nama_d, kode_d, score_d
        parts = kode_d.split(".")
        if not result["kecamatan"]:
            row = df_kec[df_kec["kode"] == ".".join(parts[:3])]
            if not row.empty:
                result["kecamatan"], result["kode_kec"], result["score_kec"] = row.iloc[0]["nama"], ".".join(parts[:3]), score_d
        if not result["kabkota"]:
            row = df_kabkota[df_kabkota["kode"] == ".".join(parts[:2])]
            if not row.empty:
                result["kabkota"], result["kode_kabkota"], result["score_kabkota"] = row.iloc[0]["nama"], ".".join(parts[:2]), score_d
        if not result["provinsi"]:
            row = df_prov[df_prov["kode"] == parts[0]]
            if not row.empty:
                result["provinsi"], result["kode_prov"], result["score_prov"] = row.iloc[0]["nama"], parts[0], score_d

    return result
