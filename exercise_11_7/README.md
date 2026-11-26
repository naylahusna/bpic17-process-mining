# Exercise 11.7 A–E · Anggota 2

Panel menghitung lima jawaban dari pandas DataFrame dan menyediakan daftar case ID, durasi, aturan filter, pencarian, serta tombol rincian. Setiap case dihitung sekali per butir. Case dapat lolos C dan D sekaligus. Untuk E, event akhir ditentukan dari timestamp terbaru. Jika timestamp sama, urutan event pada log menentukan posisi akhirnya. Durasi dihitung dari trace lengkap dalam hari, dengan timestamp dinormalisasi ke UTC.

## Jalankan mandiri

Dari direktori utama repo, gunakan CPython dengan Tkinter dan jalankan:

```powershell
python -m pip install pm4py==2.7.17
python -m exercise_11_7 "C:\jalur\BPI Challenge 2017.xes"
python -m exercise_11_7 "C:\jalur\BPI Challenge 2017.xes" --gui
python -m unittest exercise_11_7.test_analysis
```

Ganti jalur dengan lokasi file XES di komputer. Pratinjau juga menerima `.xes.gz`. Pada GUI, pilih **Jalankan analisis**, lalu pilih baris A–E. Gunakan **Lihat rincian case** untuk memeriksa ID yang dikirim dari panel.

## Integrasi setelah aplikasi kelompok siap

- Impor `prepare_log` dari `ordering_11_22.py`, lalu buat `Exercise117Panel(parent, on_open_case, prepare_log=prepare_log)`. Panggil `panel.set_log(df)` setiap kali log aktif berubah.
- Panel memerlukan kolom `case:concept:name`, `concept:name`, dan `time:timestamp`. Kolom `lifecycle:transition` dan `org:resource` boleh tetap disertakan. Fungsi bersama menerima DataFrame dan mengembalikan DataFrame event dalam urutan yang disepakati. Untuk E, panel memakai baris terakhir per case hasil fungsi tersebut.
- Untuk CSV, panggil `panel.export_payload()`. Hasilnya tuple `(summary_dict, df_case_terpilih)`. Ringkasan berisi `exercise`, `question`, `rule`, `case_count`, dan `mean_cycle_time_days`. Tabel memuat `case:concept:name` dan `cycle_time_days` untuk seluruh case dari butir aktif. Sebelum analisis, hasilnya ringkasan kosong dan tabel kosong.
- Callback `on_open_case(case_id)` menerima ID saat pengguna meminta rincian. Hubungkan ke Case Explorer.
- `panel.answers` berisi hasil A–E, dan `panel.selected_answer()` mengembalikan hasil butir terpilih. Di tiap hasil tersedia `rule`, `count`, `mean_days`, dan daftar `cases` yang berisi `case_id` dan `days`.
- Fungsi `cycle_time_days(start, end)` tersedia untuk dipakai oleh Overview.

Sumber pembanding hasil uji adalah materi BPIC-2017 dari Kulon, Exercise 11.7 dan Solution 11.7, halaman 6–7. Aplikasi menghitung hasil dari file yang diberikan.

## Hasil uji BPIC17

| Butir | Hasil dari XES | Acuan slide |
| --- | --- | --- |
| A | 31.509 case | 31.509 case |
| B | 21,900 hari | 21,9 hari |
| C | 17.228 case, 18,134 hari | 17.228 case, 18,1 hari |
| D | 3.720 case, 16,878 hari | 3.720 case, 16,8 hari |
| E | 4.436 case, 23,510 hari | 4.436 case, 23 hari |

Jumlah case cocok pada semua butir. Durasi D dan E berbeda sekitar 0,078 dan 0,510 hari dari angka pada slide. Pembacaan langsung XML tanpa PM4Py menghasilkan durasi yang sama dengan aplikasi. Verifikasi juga menunjukkan bahwa urutan file dan pengurutan stabil berdasarkan timestamp menghasilkan himpunan jumlah dan rata-rata yang sama untuk E. Slide tidak merinci presisi atau prosedur perhitungannya, sehingga penyebab selisih tidak dapat dipastikan. Aplikasi melaporkan durasi dari timestamp awal dan akhir trace lengkap.

Uji sintetis mencakup aktivitas berulang, kategori yang bertumpang tindih, O_Cancelled di tengah trace, timestamp sama, case satu event, grup kosong, timestamp tidak valid, dan case ID ganda. Panel diuji untuk menampilkan A–E, berpindah halaman, mencari case, mengirim ID ke callback, dan mereset hasil saat log berganti.
