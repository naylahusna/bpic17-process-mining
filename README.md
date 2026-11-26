# BPIC17 Process Mining

Proyek kelompok Data Mining Tahap 1. Aplikasi desktop Python dan PM4Py menganalisis proses pengajuan pinjaman dari event log BPI Challenge 2017. Pengguna memilih file XES, menjalankan analisis, memeriksa event yang mendukung hasil, dan mengekspor ringkasan serta daftar case.

## Dataset

Gunakan event log lengkap **BPI Challenge 2017** versi 1, yang dipublikasikan oleh Boudewijn van Dongen. Unduh `BPI Challenge 2017.xes.gz`, ekstrak menjadi `.xes`, dan simpan secara lokal. Untuk pengujian akhir, gunakan versi dataset yang ditetapkan dosen. [Dataset resmi 4TU.ResearchData](https://doi.org/10.4121/uuid:5f3067df-f10b-45da-b98b-86ae4c7a310b)

## Cara kerja aplikasi

1. **Impor XES.** Pilih file melalui dialog aplikasi. PM4Py membaca log, lalu aplikasi memvalidasi atribut wajib dan menampilkan status impor.
2. **Periksa Overview.** Lihat jumlah case dan event, frekuensi aktivitas, rentang waktu, rata-rata cycle time, serta daftar durasi per case.
3. **Pilih latihan dan jalankan analisis.** Panel menghitung hasil dari log aktif dan menampilkan aturan, jumlah case, serta metrik yang diminta. Jalankan ulang analisis dari log yang sama jika diperlukan.
4. **Periksa bukti di Case Explorer.** Cari atau pilih case ID dari hasil analisis. Tinjau timestamp, aktivitas, lifecycle, dan resource jika tersedia. Gunakan event yang ditandai untuk memeriksa aturan yang dipakai.
5. **Ekspor CSV.** Simpan ringkasan jawaban dan daftar case terpilih untuk pelaporan.

### Aturan analisis

| Fitur | Hasil dan aturan |
| --- | --- |
| **[11.7 A–E (F03)](exercise_11_7/README.md)** | Hitung jumlah case unik dan rata-rata cycle time seluruh case. Untuk C dan D, pilih case yang memuat `O_Accepted` atau `O_Refused`. Untuk E, pilih case yang event terakhirnya `O_Cancelled`. Tampilkan jumlah dan rata-rata durasi untuk masing-masing kelompok. |
| **11.15 (F04)** | Hitung case dengan minimal dua event `W_Assess Potential Fraud` berstatus `complete`. Tampilkan jumlah kemunculan dan event bukti. |
| **11.18 (F05)** | Terapkan aturan `complete`, lalu cari minimal dua penyelesaian oleh resource teridentifikasi yang sama dalam satu case. Tampilkan resource, jumlah penyelesaian, dan event bukti. |
| **11.22 (F06)** | Cari `O_Cancelled` yang kemudian diikuti `O_Accepted` dalam trace, termasuk bila ada event penyela. Tampilkan pasangan event bukti, jumlah case cocok, jumlah seluruh case pada log aktif, dan persentasenya. |

PM4Py membaca XES dan aplikasi meneruskan log aktif ke panel sebagai pandas DataFrame. Kolom utamanya adalah `case:concept:name`, `concept:name`, dan `time:timestamp`. Atribut `lifecycle:transition` serta `org:resource` digunakan ketika tersedia. Event diurutkan secara konsisten dan event dengan timestamp sama mengikuti urutan asli di XES. Cycle time dihitung dari timestamp awal dan akhir trace lengkap dalam satuan hari. Agregat dihitung per case.

## Instalasi dan menjalankan aplikasi

Aplikasi gabungan sedang dalam tahap integrasi. Perintah instalasi dan peluncuran akan dicantumkan di bagian ini setelah versi gabungan bisa dijalankan dari salinan repo baru. Konfigurasi dependensi dan versi Python yang diuji akan disertakan bersama kode aplikasi.

## Struktur dan pengujian

| Komponen | Peran |
| --- | --- |
| Aplikasi utama dan Overview (F01–F02) | Mengelola impor, validasi, status, log aktif, dan statistik dasar. |
| Panel analisis (F03–F06) | Mengolah log aktif sesuai aturan tiap latihan dan menyediakan hasil serta bukti case. |
| Case Explorer dan ekspor (F07) | Membuka trace dari hasil setiap panel dan mengekspor ringkasan serta daftar case. |

Pengujian akhir menggunakan BPIC17 melalui alur lengkap dari impor hingga ekspor. Impor ulang file yang sama untuk memeriksa apakah hasil dapat direproduksi. Uji juga log sintetis untuk memastikan semantik filter pada kasus tepi, seperti timestamp yang sama, event berulang, resource kosong, dan pasangan event yang tidak bersebelahan. Hasil uji, perbandingan dengan materi latihan, contoh bukti case, tangkapan layar, dan kontribusi anggota disertakan dalam laporan proyek.
