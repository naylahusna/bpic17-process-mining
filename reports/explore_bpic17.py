import os
import sys
import pandas as pd
import pm4py

DATASET_PATH = "data/raw/BPI Challenge 2017.xes"
REPORT_PATH = "reports/anggota3_dataset_profile.md"

print(f"Reading dataset with PM4Py from {DATASET_PATH}...")
log = pm4py.read_xes(DATASET_PATH)
df = log if isinstance(log, pd.DataFrame) else pm4py.convert_to_dataframe(log)
print("Dataset read complete!")

case_col = "case:concept:name"
act_col = "concept:name"
life_col = "lifecycle:transition"
res_col = "org:resource"

total_cases = df[case_col].nunique() if case_col in df.columns else 0
total_events = len(df)
all_columns = list(df.columns)

has_case = case_col in df.columns
has_act = act_col in df.columns
has_life = life_col in df.columns
has_res = res_col in df.columns

# Lifecycle distribution across entire log
life_dist = df[life_col].value_counts(dropna=False).to_dict() if has_life else {}

# Resource stats across entire log
res_count = df[res_col].nunique(dropna=True) if has_res else 0
res_missing_total = df[res_col].isna().sum() if has_res else 0

# Target activity: match case-insensitively
# In XES, exact name is 'W_Assess potential fraud'
df_target = df[df[act_col].astype(str).str.strip().str.lower() == "w_assess potential fraud"] if has_act else pd.DataFrame()
target_act_exact = df_target[act_col].iloc[0] if not df_target.empty else "W_Assess potential fraud"
target_total_freq = len(df_target)
target_cases_count = df_target[case_col].nunique() if has_case and not df_target.empty else 0

# Target activity by lifecycle
target_life_dist = df_target[life_col].value_counts(dropna=False).to_dict() if has_life and not df_target.empty else {}

# Target activity missing/empty resources
if has_res and not df_target.empty:
    target_res_isna = int(df_target[res_col].isna().sum())
    target_res_empty_str = int((df_target[res_col].astype(str).str.strip() == "").sum())
    # Count resources that are NaN, None, empty string, or lowercase 'nan'/'none'
    is_missing = df_target[res_col].isna() | (df_target[res_col].astype(str).str.strip().str.lower().isin(["", "nan", "none"]))
    target_res_missing_or_empty = int(is_missing.sum())
else:
    target_res_isna = 0
    target_res_empty_str = 0
    target_res_missing_or_empty = 0

print("Generating markdown report...")
report_content = f"""# BPIC17 Dataset Exploration & Profiling Report
**Role:** Anggota 3 (Exercise 11.15 & Exercise 11.18)  
**File Analisis:** `{DATASET_PATH}`  
**Engine:** PM4Py {pm4py.__version__} via pandas DataFrame  
**Status Ekstraksi:** Berhasil diekstrak dan diverifikasi

---

## 1. Ringkasan Umum Log
- **Total Kasus (Unique Cases):** {total_cases:,} case
- **Total Kejadian (Total Events):** {total_events:,} event
- **Total Kolom Atribut:** {len(all_columns)}

---

## 2. Verifikasi Keberadaan Atribut Kunci
| Atribut | Fungsi | Status | Keterangan |
| :--- | :--- | :--- | :--- |
| `case:concept:name` | Identitas case | {"✅ Ditemukan" if has_case else "❌ Tidak Ditemukan"} | Kolom pengelompokan trace per case |
| `concept:name` | Nama aktivitas | {"✅ Ditemukan" if has_act else "❌ Tidak Ditemukan"} | Menyimpan nama aktivitas |
| `lifecycle:transition` | Status aktivitas | {"✅ Ditemukan" if has_life else "❌ Tidak Ditemukan"} | Status transisi siklus hidup event |
| `org:resource` | Identitas resource | {"✅ Ditemukan" if has_res else "❌ Tidak Ditemukan"} | Identitas agen/user penanggung jawab event |

### Seluruh Atribut yang Tersedia pada Event Log:
```text
{', '.join(all_columns)}
```

---

## 3. Analisis Atribut `lifecycle:transition`
Distribusi seluruh nilai lifecycle pada keseluruhan event log ({total_events:,} events):
| Nilai Lifecycle | Frekuensi | Persentase |
| :--- | :--- | :--- |
"""

for k, v in sorted(life_dist.items(), key=lambda x: str(x[0])):
    pct = (v / total_events) * 100
    report_content += f"| `{k}` | {v:,} | {pct:.2f}% |\n"

report_content += f"""
> [!NOTE]
> Pada dataset BPIC17, status transisi siklus hidup dicatat dalam huruf kecil (*lowercase*), yaitu:
> - `complete`: menandakan penyelesaian aktivitas ({life_dist.get('complete', 0):,} events).
> - `schedule`: penjadwalan aktivitas ({life_dist.get('schedule', 0):,} events).
> - `start`: dimulainya pengerjaan aktivitas ({life_dist.get('start', 0):,} events).
> - `suspend`: penundaan aktivitas ({life_dist.get('suspend', 0):,} events).
> - `resume`: pelanjutan aktivitas ({life_dist.get('resume', 0):,} events).
> - `ate_abort`: pembatalan aktivitas ({life_dist.get('ate_abort', 0):,} events).
> - `withdraw`: penarikan aktivitas ({life_dist.get('withdraw', 0):,} events).

---

## 4. Analisis Atribut `org:resource`
- **Jumlah Resource Unik Teridentifikasi:** {res_count:,} resource
- **Total Event dengan Resource Kosong/NaN:** {res_missing_total:,} ({(res_missing_total / total_events) * 100:.2f}%)
- **Format Resource:** Berformat string unik seperti `User_1`, `User_2`, ..., `User_149`.

---

## 5. Eksplorasi Khusus Aktivitas Target: `{target_act_exact}`
Aktivitas target untuk **Exercise 11.15** dan **Exercise 11.18** tercatat di file XES dengan nama eksak:
**`{target_act_exact}`** *(perhatikan huruf kecil pada kata 'potential' dan 'fraud')*.

- **Total Frekuensi Kejadian Target:** {target_total_freq:,} event
- **Jumlah Case yang Memuat Aktivitas Ini:** {target_cases_count:,} case

### Rincian Kejadian Target Berdasarkan Lifecycle:
| Nilai Lifecycle | Jumlah Event | Keterangan untuk Analisis |
| :--- | :--- | :--- |
"""

for k, v in sorted(target_life_dist.items(), key=lambda x: str(x[0])):
    is_complete = str(k).strip().lower() == "complete"
    ket = "**DIHITUNG** (Representasi penyelesaian aktivitas)" if is_complete else "DIABAIKAN (bukan status penyelesaian)"
    report_content += f"| `{k}` | {v:,} | {ket} |\n"

report_content += f"""
### Analisis Resource pada Aktivitas Target:
- **Event `{target_act_exact}` dengan Resource NaN/None:** {target_res_isna:,}
- **Event `{target_act_exact}` dengan Resource String Kosong:** {target_res_empty_str:,}
- **Total Resource Tidak Valid (Kosong/NaN):** {target_res_missing_or_empty:,}

---

## 6. Kesimpulan & Aturan Implementasi Logika Anggota 3
1. **Normalisasi String Aktivitas:**
   - Karena pada soal tertulis `W_Assess Potential Fraud` sedangkan pada dataset tertulis `W_Assess potential fraud`, fungsi filter harus menerapkan normalisasi *case-insensitive* `.str.strip().str.lower() == 'w_assess potential fraud'`.
2. **Normalisasi dan Filter Lifecycle `complete`:**
   - Hanya event dengan `lifecycle:transition` bernilai `complete` (diuji dengan `.str.strip().str.lower() == 'complete'`) yang dihitung sebagai penyelesaian. Status `schedule`, `start`, `suspend`, `resume`, `ate_abort`, `withdraw` wajib diabaikan.
3. **Penanganan Resource Kosong (Exercise 11.18):**
   - Resource kosong (`NaN`, `None`, string kosong `""`, atau string `"nan"`/`"none"`) **wajib dikeluarkan** dari pengelompokan.
   - Dua kejadian berstatus `complete` dengan resource kosong **TIDAK BOLEH** dianggap dieksekusi oleh resource yang sama.
4. **Perhitungan pada Level Case:**
   - Sesuai prinsip *case-level analytics*, 1 case yang memenuhi kriteria dihitung tepat 1 kali pada hasil agregat (`matched_count`).
"""

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write(report_content)

print(f"Report successfully generated at: {REPORT_PATH}")
print(f"Summary: Total Cases={total_cases:,}, Total Events={total_events:,}")
print(f"Target Activity '{target_act_exact}': Total Events={target_total_freq:,}, Cases={target_cases_count:,}")
print("Target Activity Lifecycle Breakdown:")
for k, v in target_life_dist.items():
    print(f"  - {k}: {v:,}")
print(f"Target Activity Missing Resources: {target_res_missing_or_empty:,}")
