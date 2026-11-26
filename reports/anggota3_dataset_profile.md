# BPIC17 Dataset Exploration & Profiling Report
**Role:** Anggota 3 (Exercise 11.15 & Exercise 11.18)  
**File Analisis:** `data/raw/BPI Challenge 2017.xes`  
**Engine:** PM4Py 2.7.23.15 via pandas DataFrame  
**Status Ekstraksi:** Berhasil diekstrak dan diverifikasi

---

## 1. Ringkasan Umum Log
- **Total Kasus (Unique Cases):** 31,509 case
- **Total Kejadian (Total Events):** 1,202,267 event
- **Total Kolom Atribut:** 19

---

## 2. Verifikasi Keberadaan Atribut Kunci
| Atribut | Fungsi | Status | Keterangan |
| :--- | :--- | :--- | :--- |
| `case:concept:name` | Identitas case | ✅ Ditemukan | Kolom pengelompokan trace per case |
| `concept:name` | Nama aktivitas | ✅ Ditemukan | Menyimpan nama aktivitas |
| `lifecycle:transition` | Status aktivitas | ✅ Ditemukan | Status transisi siklus hidup event |
| `org:resource` | Identitas resource | ✅ Ditemukan | Identitas agen/user penanggung jawab event |

### Seluruh Atribut yang Tersedia pada Event Log:
```text
Action, org:resource, concept:name, EventOrigin, EventID, lifecycle:transition, time:timestamp, case:LoanGoal, case:ApplicationType, case:concept:name, case:RequestedAmount, FirstWithdrawalAmount, NumberOfTerms, Accepted, MonthlyCost, Selected, CreditScore, OfferedAmount, OfferID
```

---

## 3. Analisis Atribut `lifecycle:transition`
Distribusi seluruh nilai lifecycle pada keseluruhan event log (1,202,267 events):
| Nilai Lifecycle | Frekuensi | Persentase |
| :--- | :--- | :--- |
| `ate_abort` | 85,224 | 7.09% |
| `complete` | 475,306 | 39.53% |
| `resume` | 127,160 | 10.58% |
| `schedule` | 149,104 | 12.40% |
| `start` | 128,227 | 10.67% |
| `suspend` | 215,402 | 17.92% |
| `withdraw` | 21,844 | 1.82% |

> [!NOTE]
> Pada dataset BPIC17, status transisi siklus hidup dicatat dalam huruf kecil (*lowercase*), yaitu:
> - `complete`: menandakan penyelesaian aktivitas (475,306 events).
> - `schedule`: penjadwalan aktivitas (149,104 events).
> - `start`: dimulainya pengerjaan aktivitas (128,227 events).
> - `suspend`: penundaan aktivitas (215,402 events).
> - `resume`: pelanjutan aktivitas (127,160 events).
> - `ate_abort`: pembatalan aktivitas (85,224 events).
> - `withdraw`: penarikan aktivitas (21,844 events).

---

## 4. Analisis Atribut `org:resource`
- **Jumlah Resource Unik Teridentifikasi:** 149 resource
- **Total Event dengan Resource Kosong/NaN:** 0 (0.00%)
- **Format Resource:** Berformat string unik seperti `User_1`, `User_2`, ..., `User_149`.

---

## 5. Eksplorasi Khusus Aktivitas Target: `W_Assess potential fraud`
Aktivitas target untuk **Exercise 11.15** dan **Exercise 11.18** tercatat di file XES dengan nama eksak:
**`W_Assess potential fraud`** *(perhatikan huruf kecil pada kata 'potential' dan 'fraud')*.

- **Total Frekuensi Kejadian Target:** 3,282 event
- **Jumlah Case yang Memuat Aktivitas Ini:** 303 case

### Rincian Kejadian Target Berdasarkan Lifecycle:
| Nilai Lifecycle | Jumlah Event | Keterangan untuk Analisis |
| :--- | :--- | :--- |
| `ate_abort` | 42 | DIABAIKAN (bukan status penyelesaian) |
| `complete` | 282 | **DIHITUNG** (Representasi penyelesaian aktivitas) |
| `resume` | 996 | DIABAIKAN (bukan status penyelesaian) |
| `schedule` | 327 | DIABAIKAN (bukan status penyelesaian) |
| `start` | 355 | DIABAIKAN (bukan status penyelesaian) |
| `suspend` | 1,277 | DIABAIKAN (bukan status penyelesaian) |
| `withdraw` | 3 | DIABAIKAN (bukan status penyelesaian) |

### Analisis Resource pada Aktivitas Target:
- **Event `W_Assess potential fraud` dengan Resource NaN/None:** 0
- **Event `W_Assess potential fraud` dengan Resource String Kosong:** 0
- **Total Resource Tidak Valid (Kosong/NaN):** 0

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
