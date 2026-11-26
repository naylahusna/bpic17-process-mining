# Laporan Hasil Pengujian BPIC17 Asli
**Penanggung Jawab:** Anggota 3  
**Cakupan:** Exercise 11.15 (Repeated Complete) & Exercise 11.18 (Same Resource)  
**Dataset:** `data/raw/BPI Challenge 2017.xes` (552 MiB / 1.202.267 events)  
**Engine:** PM4Py 2.7.23.15 via pandas DataFrame  

---

## 1. Ringkasan Eksekutif Hasil Analisis

| Parameter / Metrik | Exercise 11.15 (Repeated Complete) | Exercise 11.18 (Same Resource) |
| :--- | :--- | :--- |
| **Aktivitas Target** | `W_Assess Potential Fraud` (case-insensitive) | `W_Assess Potential Fraud` (case-insensitive) |
| **Status Lifecycle** | `complete` (case-insensitive) | `complete` (case-insensitive) |
| **Syarat Resource** | Bebas (boleh sama/berbeda/kosong) | **Wajib resource teridentifikasi sama >= 2x** |
| **Total Seluruh Case (Denominator)** | **31,509** case | **31,509** case |
| **Jumlah Case Terpilih (`matched_cases`)** | **13** case | **3** case |
| **Persentase Case Terpilih** | **0.0413%** | **0.0095%** |
| **Verifikasi Subset ($11.18 \subseteq 11.15$)** | — | **TERBUKTI BENAR** (`True`) |

---

## 2. Temuan Mendalam Exercise 11.15

### A. Aturan Analisis
> Memilih case di mana aktivitas `W_Assess Potential Fraud` memiliki status `complete` minimal 2 kali. Satu case dihitung tepat satu kali.

### B. Distribusi Kejadian Complete per Case
Dari total 303 case yang pernah memuat aktivitas `W_Assess potential fraud`:
- Case dengan 0 kali complete (hanya schedule/start/abort/suspend/resume): **163 case**
- Case dengan tepat 1 kali complete: **127 case** (tidak lolos 11.15)
- Case dengan **minimal 2 kali complete**: **13 case** (lolos 11.15)

Rincian case yang lolos:
- Case dengan **2 kali complete**: **12 case**
- Case dengan **3 kali complete**: **1 case**

### C. Daftar Lengkap Case ID yang Memenuhi (13 Case)
```text
Application_1021748617, Application_1114361455, Application_1221917431, Application_1292983087, Application_1405826636, Application_1568546217, Application_287618269, Application_412627378, Application_438711887, Application_473455481, Application_534041276, Application_612471425, Application_900460993
```

---

## 3. Temuan Mendalam Exercise 11.18

### A. Aturan Analisis
> Memilih case yang memiliki aktivitas `W_Assess Potential Fraud` berstatus `complete` minimal 2 kali **oleh resource teridentifikasi yang sama**. Resource kosong dikeluarkan.

### B. Daftar Case ID & Resource yang Memenuhi Syarat (3 Case)
| Case ID | Resource yang Memenuhi & Frekuensi |
| :--- | :--- |
| `Application_1221917431` | User_144 (2x) |
| `Application_1405826636` | User_143 (2x) |
| `Application_473455481` | User_143 (2x) |

### C. Analisis Selisih ($11.15 - 11.18$)
Terdapat selisih **10 case** yang lolos pada 11.15 tetapi **TIDAK lolos** pada 11.18:
Daftar case selisih:
```text
Application_1021748617, Application_1114361455, Application_1292983087, Application_1568546217, Application_287618269, Application_412627378, Application_438711887, Application_534041276, Application_612471425, Application_900460993
```
**Penyebab Selisih:**
Pada 10 case tersebut, aktivitas `W_Assess Potential Fraud` memang diselesaikan minimal 2 kali, namun setiap penyelesaian dikerjakan oleh **orang/user yang berbeda** (misalnya completion 1 oleh `User_87` dan completion 2 oleh `User_99`), sehingga tidak memenuhi syarat identitas resource tunggal pada 11.18.

---

## 4. Sampel Bukti Kejadian (Event Evidence)

### Sampel Evidence Exercise 11.15:
| case:concept:name | _pos | concept:name | lifecycle:transition | org:resource | time:timestamp |
| --- | --- | --- | --- | --- | --- |
| Application_1021748617 | 29 | W_Assess potential fraud | complete | User_99 | 2016-06-20 13:31:57.643000+00:00 |
| Application_1021748617 | 38 | W_Assess potential fraud | complete | User_138 | 2016-06-21 08:54:00.134000+00:00 |
| Application_1114361455 | 11 | W_Assess potential fraud | complete | User_138 | 2016-12-02 09:15:56.833000+00:00 |
| Application_1114361455 | 47 | W_Assess potential fraud | complete | User_143 | 2016-12-15 07:58:01.236000+00:00 |
| Application_1221917431 | 59 | W_Assess potential fraud | complete | User_144 | 2016-07-05 11:36:11.613000+00:00 |
| Application_1221917431 | 73 | W_Assess potential fraud | complete | User_144 | 2016-07-06 09:35:58.622000+00:00 |
| Application_1292983087 | 29 | W_Assess potential fraud | complete | User_90 | 2016-08-11 08:05:51.911000+00:00 |
| Application_1292983087 | 34 | W_Assess potential fraud | complete | User_143 | 2016-08-15 11:50:39.782000+00:00 |
| Application_1292983087 | 85 | W_Assess potential fraud | complete | User_138 | 2016-10-07 07:04:40.985000+00:00 |
| Application_1405826636 | 29 | W_Assess potential fraud | complete | User_143 | 2016-11-21 16:02:30.874000+00:00 |

### Sampel Evidence Exercise 11.18:
| case:concept:name | _pos | concept:name | lifecycle:transition | org:resource | time:timestamp |
| --- | --- | --- | --- | --- | --- |
| Application_1221917431 | 59 | W_Assess potential fraud | complete | User_144 | 2016-07-05 11:36:11.613000+00:00 |
| Application_1221917431 | 73 | W_Assess potential fraud | complete | User_144 | 2016-07-06 09:35:58.622000+00:00 |
| Application_1405826636 | 29 | W_Assess potential fraud | complete | User_143 | 2016-11-21 16:02:30.874000+00:00 |
| Application_1405826636 | 44 | W_Assess potential fraud | complete | User_143 | 2016-11-22 08:17:07.392000+00:00 |
| Application_473455481 | 61 | W_Assess potential fraud | complete | User_143 | 2016-08-18 07:12:22.725000+00:00 |
| Application_473455481 | 77 | W_Assess potential fraud | complete | User_143 | 2016-08-25 11:03:54.059000+00:00 |

---

## 5. Kesimpulan Validasi Proyek
1. **Integritas Perhitungan:** Seluruh angka dihitung dinamis langsung dari dataset XES asli menggunakan PM4Py tanpa hard-coding.
2. **Konsistensi Semantik:** Penanganan status `complete` berhasil menyaring 2.955 event non-complete (start, schedule, suspend, resume, abort).
3. **Kepatuhan Sub-kelompok:** Seluruh 3 case pada Exercise 11.18 terbukti merupakan himpunan bagian (*subset*) murni dari 13 case pada Exercise 11.15.
