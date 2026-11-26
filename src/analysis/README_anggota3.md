# Modul Analisis Anggota 3 — BPIC17

Modul ini bertanggung jawab atas penyelesaian:
1. **Exercise 11.15 — Repeated Complete** (F04)
2. **Exercise 11.18 — Same Resource** (F05)

Aplikasi dan modul dibangun di atas Python dan PM4Py, memproses event log BPIC17 secara dinamis tanpa angka *hard-coded*.

---

## 1. Definisi Latihan

### Exercise 11.15 (Repeated Complete)
- **Pertanyaan:** Berapa case di mana aktivitas `W_Assess Potential Fraud` diselesaikan minimal $2\times$?
- **Aturan Analisis:**
  - Menghitung hanya kejadian (*occurrence*) berstatus lifecycle `complete`.
  - Satu case dihitung tepat satu kali pada hasil agregat (`matched_cases`), tidak peduli berapa kali aktivitas tersebut berulang di atas 2 kali.
  - Resource pelaksana bebas (boleh sama, berbeda, atau kosong).

### Exercise 11.18 (Same Resource)
- **Pertanyaan:** Berapa case di mana aktivitas tersebut selesai minimal $2\times$ oleh resource yang sama?
- **Aturan Analisis:**
  - Melanjutkan aturan filter `complete` dari 11.15.
  - Memilih case yang memiliki minimal 2 kejadian `complete` yang dikerjakan oleh **resource teridentifikasi yang sama** (`org:resource`).
  - Resource kosong (`NaN`, `None`, `""`, atau string `"nan"`) **wajib dikeluarkan** dari pengelompokan dan tidak boleh dianggap sebagai resource yang sama.
  - Satu case dihitung tepat satu kali, meskipun dalam satu case terdapat lebih dari satu resource yang memenuhi syarat.

---

## 2. Penjelasan Algoritma & Normalisasi

### A. Penanganan Nama Aktivitas
Pada materi tugas tertulis `W_Assess Potential Fraud` (huruf kapital), sedangkan pada file dataset asli BPIC17 tercatat sebagai `W_Assess potential fraud` (huruf kecil pada 'potential' dan 'fraud'). Oleh karena itu, modul menerapkan normalisasi *case-insensitive* dan *whitespace trimming*:
```python
act_mask = df[ACT].astype(str).str.strip().str.lower() == "w_assess potential fraud"
```

### B. Penanganan Lifecycle (`complete`)
Event log BPIC17 mencatat berbagai transisi siklus hidup: `complete`, `schedule`, `start`, `suspend`, `resume`, `ate_abort`, dan `withdraw`. Sesuai instruksi pedagogis, status selain `complete` bukan merupakan penyelesaian pekerjaan. Filter lifecycle diterapkan secara ketat:
```python
life_mask = df[LIFE].astype(str).str.strip().str.lower() == "complete"
```

### C. Penanganan Resource Kosong (Exercise 11.18)
Fungsi `is_valid_resource(res)` memastikan nilai kosong tidak lolos:
```python
def is_valid_resource(res: object) -> bool:
    if pd.isna(res) or res is None:
        return False
    s = str(res).strip()
    return s != "" and s.lower() not in ("nan", "none", "null")
```

### D. Pengurutan Trace & Bukti Posisi Event
Modul menggunakan fungsi `prepare_log(df)` yang identik dengan Anggota 4 dan Anggota 2:
```python
d = d.sort_values([CASE, TS, ORIG], kind="mergesort").reset_index(drop=True)
d[POS] = d.groupby(CASE, sort=False).cumcount()
```
Pengurutan stabil berdasarkan timestamp dan posisi baris asli XES menghasilkan indeks `_pos` (0-based) yang sinkron dengan penandaan warna dan timeline pada **Case Explorer**.

---

## 3. Format Output & Interface Integrasi

### A. Dataclass Hasil
- `Exercise1115Result`:
  - `exercise`: `"11.15"`
  - `rule`: Penjelasan aturan filter
  - `total_cases`: Total seluruh case unik pada log aktif (denominator)
  - `matched_count`: Jumlah case yang lolos
  - `matched_case_ids`: List Case ID terpilih
  - `occurrence_counts`: Dict pemetaan `{case_id: complete_count}`
  - `summary_df`: DataFrame tabel hasil dengan kolom `case:concept:name` dan `complete_count`
  - `evidence_df`: DataFrame event asli yang menjadi bukti
  - `evidence_by_case`: Dict pemetaan untuk Case Explorer `{case_id: {pos: "Complete #k"}}`
  - `summary_dict()`: Dict metrik ringkas untuk ekspor CSV
  - `export_payload()`: Mengembalikan `(summary_dict, summary_df)`

- `Exercise1118Result`:
  - `exercise`: `"11.18"`
  - `rule`: Penjelasan aturan filter
  - `total_cases`: Denominator
  - `matched_count`: Jumlah case yang lolos
  - `matched_case_ids`: List Case ID terpilih
  - `qualifying_resources`: Dict `{case_id: [{"resource_id": r, "count": c}, ...]}`
  - `summary_df`: DataFrame 1 baris per case dengan kolom `case:concept:name`, `resource_id`, dan `complete_count`
  - `evidence_df`: DataFrame event bukti
  - `evidence_by_case`: Dict pemetaan untuk Case Explorer `{case_id: {pos: "Complete #k by User_X"}}`
  - `export_payload()`: Mengembalikan `(summary_dict, summary_df)`

### B. Interface GUI (PySide6)
Dua panel GUI tersedia di `src/gui/`:
- `Panel1115` (`src/gui/panel_11_15.py`)
- `Panel1118` (`src/gui/panel_11_18.py`)

Keduanya mengintegrasikan komponen tim:
- `AnalysisInfoBar`: Menampilkan aturan, case terpilih, denominator, dan persentase.
- `CaseExplorerWidget`: Menampilkan tabel case, pencarian case ID, visualisasi timeline event, dan detail atribut trace.
- Multithreading `QThread` (`_Worker1115` & `_Worker1118`) agar GUI tetap responsif saat memproses dataset besar.

---

## 4. Cara Menjalankan

### A. Menjalankan Unit Tests (Pytest)
Dari root direktori repositori `bpic17-process-mining`:
```bash
.venv/bin/pytest tests/test_exercise_11_15.py tests/test_exercise_11_18.py -v
```

### B. Menjalankan Analisis pada Dataset Asli
```python
import pm4py
from src.analysis.exercise_11_15 import analyze_repeated_complete
from src.analysis.exercise_11_18 import analyze_same_resource

# Baca XES
log = pm4py.read_xes("data/raw/BPI Challenge 2017.xes")

# Jalankan analisis 11.15
res15 = analyze_repeated_complete(log)
print(f"11.15 Matched: {res15.matched_count} dari {res15.total_cases} case")

# Jalankan analisis 11.18
res18 = analyze_same_resource(log)
print(f"11.18 Matched: {res18.matched_count} dari {res18.total_cases} case")
```

---

## 5. Ringkasan Hasil pada BPIC17 Asli

- **Total Case:** 31.509
- **Total Event:** 1.202.267
- **Total Event `W_Assess potential fraud`:** 3.282 event (tersebar di 303 case)
- **Total Event Berstatus `complete`:** 282 event
- **Hasil Exercise 11.15:** **13 case** (0,0413%)
  - 12 case memiliki tepat 2 complete
  - 1 case memiliki 3 complete
- **Hasil Exercise 11.18:** **3 case** (0,0095%)
  - Seluruh 3 case merupakan bagian (*subset*) dari 13 case pada Exercise 11.15.
  - Resource pelaksana pada 3 case tersebut adalah `User_144` (1 case) dan `User_143` (2 case).
