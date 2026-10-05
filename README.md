# Auto Parsing Address

Pipeline berbasis aturan (regex + fuzzy matching) untuk memecah alamat Indonesia yang ditulis bebas menjadi kolom terstruktur: detail alamat (jalan, nomor, RT/RW, gedung, lantai, blok, kavling, kode pos) dan wilayah administratif (provinsi, kabupaten/kota, kecamatan, desa/kelurahan) lengkap dengan kode wilayahnya.

## Daftar Isi

- [Cara Kerja](#cara-kerja)
- [Struktur Proyek](#struktur-proyek)
- [Prasyarat](#prasyarat)
- [Instalasi](#instalasi)
- [Menyiapkan Database](#menyiapkan-database)
- [Menjalankan Pipeline](#menjalankan-pipeline)
- [Format Input](#format-input)
- [Format Output](#format-output)
- [Contoh Hasil](#contoh-hasil)
- [Masalah yang Diketahui](#masalah-yang-diketahui)
- [Notebook Eksperimen](#notebook-eksperimen)

## Cara Kerja

```
CSV alamat ──► preprocessing ──► ekstraksi detail ──► pencocokan wilayah ──► CSV + Excel
                    │              (regex)             (exact + fuzzy)
                    ▼
        PostgreSQL: master wilayah & kode pos
```

1. **Preprocessing** — master wilayah dan kode pos dimuat dari PostgreSQL, nama diseragamkan ke huruf besar, lalu dipecah per level (provinsi, kab/kota, kecamatan, desa). Tiap nama diberi versi "inti" tanpa kata administratif seperti `KOTA`, `KABUPATEN`, `ADMINISTRASI`.
2. **Ekstraksi detail** — regex mengambil bagian alamat secara berurutan: kode pos, RT/RW, nomor, lantai, gedung, jalan, blok, kavling. Setiap bagian yang ditemukan dibuang dari teks; sisanya menjadi `remaining_text`.
3. **Pencocokan wilayah** — `remaining_text` dicocokkan ke master wilayah lewat salah satu dari dua jalur:
   - **`with_postcode`** — kode pos ditemukan dan ada di master. Kandidat desa dipersempit ke desa dengan kode pos tersebut, lalu level di atasnya diturunkan dari kode desa. Kalau tidak ada desa yang cocok, wilayah diisi sejauh prefiks kode yang sama di semua kandidat.
   - **`without_postcode`** — pencocokan bertingkat dari provinsi → kab/kota → kecamatan → desa. Setiap level yang cocok mempersempit kandidat level berikutnya, dan level yang kosong diturunkan dari kode level di bawahnya.
4. **Penyimpanan** — hasil digabung dengan data asli dan disimpan sebagai CSV dan Excel.

Di setiap level, pencocokan dicoba berurutan: token persis sama, lalu dua token yang digabung (misalnya `KEBON JERUK` vs `KEBONJERUK`, khusus desa), lalu fuzzy matching RapidFuzz `token_set_ratio` dengan ambang 98. Singkatan umum seperti `JAKSEL`, `JABAR`, `SBY`, dan `DIY` diperluas lebih dulu.

## Struktur Proyek

```
address-parsing/
├── main/
│   ├── main_code/
│   │   ├── pipeline/
│   │   │   ├── main.py             # entry point CLI
│   │   │   └── preprocessing.py    # muat master wilayah & CSV input
│   │   └── results/
│   │       └── results.py          # simpan hasil ke CSV & Excel
│   └── utils/
│       ├── area_extraction.py      # pencocokan wilayah (exact, bigram, fuzzy)
│       ├── detail_extraction.py    # regex jalan, nomor, RT/RW, gedung, dst.
│       ├── database.py             # koneksi PostgreSQL & query master
│       ├── library.py              # kamus singkatan provinsi & kota
│       └── base.py                 # tokenisasi & perluasan singkatan
├── master-data/
│   └── master-matched/             # data input & hasil parsing (tidak di-commit)
├── notebooks_trial_error/          # notebook eksperimen
└── README.md
```

`pipeline/import.py`, `pipeline/parsing_area.py`, dan `pipeline/parsing_detail.py` masih kosong.

## Prasyarat

- Python 3.12
- PostgreSQL berisi master wilayah dan kode pos (lihat [Menyiapkan Database](#menyiapkan-database))

## Instalasi

```bash
git clone https://github.com/tiarasabrinaa/automation-parsing-address.git
cd automation-parsing-address

python3 -m venv .venv
source .venv/bin/activate

pip install pandas sqlalchemy psycopg2-binary rapidfuzz tqdm openpyxl
```

## Menyiapkan Database

Pipeline membaca dua tabel:

| Tabel | Kolom | Isi |
| --- | --- | --- |
| `wilayah.wilayah` | `kode`, `nama` | Seluruh wilayah administratif dalam satu tabel |
| `wilayah_kodepos.wilayah_kodepos` | `kode`, `kodepos` | Kode pos per kode desa |

Level wilayah ditentukan dari jumlah segmen pada `kode`:

| Contoh kode | Level | Contoh nama |
| --- | --- | --- |
| `31` | Provinsi | Daerah Khusus Ibukota Jakarta |
| `31.71` | Kabupaten/Kota | Kota Administrasi Jakarta Pusat |
| `31.71.01` | Kecamatan | Gambir |
| `31.71.01.1001` | Desa/Kelurahan | Gambir |

Koneksi diatur lewat environment variable `WILAYAH_DATABASE_URL`:

```bash
export WILAYAH_DATABASE_URL="postgresql://<user>:<password>@localhost:5432/wilayah_db"
```

Kalau tidak diisi, nilai bawaannya `postgresql://tiarasabrina@localhost:5432/wilayah_db`.

## Menjalankan Pipeline

Jalankan dari root proyek:

```bash
python -m main.main_code.pipeline.main \
  --input "master-data/master-matched/alamat.csv" \
  --output-dir "master-data/master-matched" \
  --limit 100
```

| Argumen | Bawaan | Keterangan |
| --- | --- | --- |
| `--input` | path absolut di `main.py` | CSV berisi alamat yang akan diparsing |
| `--output-dir` | path absolut di `main.py` | Folder tujuan hasil |
| `--limit` | `50` | Jumlah baris pertama yang diproses |

Nilai bawaan `--input` dan `--output-dir` adalah path absolut di mesin pengembang, jadi isi keduanya secara eksplisit di mesin lain.

## Format Input

File CSV dengan kolom **`Alamat Lengkap`**. Kolom lain diabaikan.

## Format Output

Dua file di `--output-dir`: `parsed_master_<limit>.csv` dan `parsed_master_<limit>.xlsx`.

| Kolom | Keterangan |
| --- | --- |
| `Alamat Lengkap` | Alamat asli dari input |
| `alamat_clean` | Alamat dalam huruf besar |
| `alamat_raw` | Alamat asli sebagai teks |
| `kodepos` | Lima digit kode pos |
| `rt`, `rw` | Nomor RT dan RW |
| `no` | Nomor bangunan |
| `lantai` | Lantai |
| `gedung` | Nama gedung, menara, ruko, komplek, dan sejenisnya |
| `jalan` | Nama jalan |
| `blok`, `kav` | Blok dan kavling |
| `remaining_text` | Sisa teks setelah detail dibuang; dipakai untuk pencocokan wilayah |
| `provinsi`, `kabkota`, `kecamatan`, `desa` | Nama wilayah hasil pencocokan |
| `kode_prov`, `kode_kabkota`, `kode_kec`, `kode_desa` | Kode wilayah |
| `score_prov`, `score_kabkota`, `score_kec`, `score_desa` | Skor keyakinan per level |
| `match_path` | `with_postcode` atau `without_postcode` |

Arti skor:

| Skor | Arti |
| --- | --- |
| `100` | Cocok persis, atau diturunkan dari level lain yang cocok persis |
| `98`–`99` | Cocok lewat fuzzy matching |
| `90` | Diturunkan dari kode pos saja, tanpa nama desa yang cocok |
| `0` | Tidak ditemukan |

## Contoh Hasil

Input:

```
Cyber 2 Tower Lantai 26, Jl. H.R. Rasuna Said Blok X-5 No. 13, Kuningan Timur, Jakarta Selatan 12950
```

Output:

| Kolom | Nilai |
| --- | --- |
| `kodepos` | `12950` |
| `no` | `13` |
| `lantai` | `26` |
| `blok` | `X-5` |
| `provinsi` | `DAERAH KHUSUS IBUKOTA JAKARTA` (`31`) |
| `kabkota` | `KOTA ADMINISTRASI JAKARTA SELATAN` (`31.74`) |
| `kecamatan` | `SETIABUDI` (`31.74.02`) |
| `desa` | `KUNINGAN TIMUR` (`31.74.02.1008`) |
| `match_path` | `with_postcode` |

## Masalah yang Diketahui

- **Nama tabel kode pos.** `main/utils/database.py` membaca `wilayah_kodepos.wilayah_kodepos`. Kalau tabel di database bernama lain (misalnya `wilayah_kodepos.kodepos`), pipeline berhenti dengan error `relation does not exist`.
- **Pembacaan kolom alamat.** `parse_addresses` di `main.py` mengambil kolom dengan nama `Alamat_Lengkap`, sedangkan kolomnya bernama `Alamat Lengkap`, sehingga pipeline berhenti dengan `AttributeError`.
- **Nama jalan dan gedung.** Regex jalan dan gedung saat ini menangkap kata kuncinya, bukan namanya: `jalan` terisi `JL`/`JALAN`, `gedung` terisi kata kunci atau kosong, dan nama aslinya masih tertinggal di `remaining_text`.
- **Alamat tanpa kode pos.** Pencocokan nama saja bisa salah wilayah ketika nama jalan sama dengan nama desa di daerah lain.
- **`docker-compose.yml`** berasal dari proyek lain (MongoDB + backend FastAPI) dan tidak dipakai pipeline ini.
- Belum ada `requirements.txt`; dependensi dipasang manual seperti di [Instalasi](#instalasi).

## Notebook Eksperimen

Folder `notebooks_trial_error/` berisi percobaan sebelum kode dipindah ke `main/`:

| Folder | Isi |
| --- | --- |
| `regex/` | Pengembangan dan debugging pendekatan regex yang sekarang dipakai pipeline |
| `llm_qwen/` | Percobaan parsing alamat dengan LLM Qwen, beserta dataset 1.000 alamat |
