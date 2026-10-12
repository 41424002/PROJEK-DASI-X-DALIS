# Dashboard Analisis ISPA Balita

Dashboard interaktif untuk menganalisis data ISPA balita berdasarkan desa, kecamatan, faktor risiko, akses puskesmas, dan kondisi sosial-ekonomi.

## Fitur

- Ringkasan indikator utama:
  - Jumlah desa
  - Jumlah penduduk
  - Jumlah balita
  - Kasus ISPA
  - Rasio ISPA per 1.000 balita
  - Kasus pneumonia dan asma
- Grafik berdasarkan:
  - Ringkasan
  - Kecamatan
  - Faktor risiko
  - Akses dan sosial-ekonomi
- Filter Kecamatan dengan dropdown dan checkbox.
- Filter Kategori kayu bakar dengan dropdown dan checkbox.
- Filter jarak ke puskesmas.
- Tabel data yang dapat diedit langsung.
- Upload dataset CSV pengganti.
- Perhitungan otomatis rasio ISPA dan kategori kayu bakar.
- Ekspor data hasil filter ke CSV.

## Struktur Proyek

```text
PROJEK-DASI-X-DALIS/
├── dashboard_ispa.py
├── dashboard_ispa.html
├── Dummy_Dataset_25Kolom_125Baris.csv
└── README.md
```

## Persyaratan Sistem

- Windows 10 atau Windows 11
- Python 3.10 atau lebih baru
- Koneksi internet saat memasang dependensi
- Browser modern seperti Google Chrome, Microsoft Edge, atau Firefox

## Instalasi

### 1. Buka folder proyek

PowerShell:

```powershell
cd "D:\Perkuliahan\SEMESTER 5\Projek Dalis X Dasi\PROJEK-DASI-X-DALIS"
```

Sesuaikan path jika folder proyek berada di lokasi lain.

### 2. Buat virtual environment

Disarankan menggunakan virtual environment agar dependensi proyek terpisah dari instalasi Python utama.

```powershell
py -m venv .venv
```

Jika perintah `py` tidak tersedia, gunakan:

```powershell
python -m venv .venv
```

### 3. Aktifkan virtual environment

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Jika PowerShell menolak eksekusi script, jalankan PowerShell sebagai user saat ini:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Kemudian aktifkan kembali:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Perbarui pip

```powershell
python -m pip install --upgrade pip
```

### 5. Pasang dependensi

```powershell
pip install streamlit plotly pandas numpy
```

## Menjalankan Proyek

### Opsi A: Menjalankan Dashboard Streamlit

Gunakan mode ini untuk dashboard utama dengan editor tabel, upload CSV, dan penyimpanan perubahan ke file sumber.

```powershell
streamlit run dashboard_ispa.py
```

Setelah berhasil dijalankan, Streamlit akan menampilkan alamat seperti:

```text
Local URL: http://localhost:8501
```

Buka alamat tersebut di browser.

Jika browser tidak terbuka otomatis, salin alamat `http://localhost:8501` ke browser.

Untuk menghentikan server:

```text
Tekan Ctrl+C pada terminal
```

### Opsi B: Membuat atau Memperbarui Dashboard HTML

Jalankan perintah berikut:

```powershell
python dashboard_ispa.py
```

Perintah tersebut akan membaca:

```text
Dummy_Dataset_25Kolom_125Baris.csv
```

dan membuat atau memperbarui:

```text
dashboard_ispa.html
```

Kemudian buka file `dashboard_ispa.html` dengan browser.

PowerShell:

```powershell
Start-Process .\dashboard_ispa.html
```

Mode HTML dapat digunakan tanpa menjalankan server Streamlit. Namun, perubahan pada mode HTML hanya tersimpan sebagai data di halaman atau sebagai file hasil unduhan, bukan langsung ke CSV sumber.

## Cara Menggunakan Dashboard

### Memilih Kecamatan

1. Buka dropdown **Kecamatan**.
2. Centang satu atau beberapa kecamatan.
3. Data, KPI, insight, dan grafik akan diperbarui otomatis.
4. Gunakan tombol **Semua kecamatan** untuk memilih seluruh kecamatan.
5. Gunakan tombol **Kosongkan kecamatan** untuk menghapus semua pilihan.

### Memilih Kategori Kayu Bakar

1. Buka dropdown **Kategori kayu bakar**.
2. Centang `Rendah`, `Tinggi`, atau keduanya.
3. Grafik dan tabel akan menampilkan data sesuai pilihan.

### Menggunakan Filter Jarak

Geser filter **Jarak maksimum** untuk menampilkan desa dengan jarak ke puskesmas sampai batas tertentu.

### Mengganti Faktor Scatter Plot

Pilih faktor yang ingin dianalisis melalui dropdown **Faktor scatter**, misalnya:

- Persentase rumah tangga memakai kayu bakar
- Persentase rumah tangga memakai LPG
- Persentase rumah tangga memiliki perokok
- Jarak ke puskesmas
- Ketinggian
- Persentase keluarga miskin
- Pendidikan ibu
- Kepadatan penduduk

## Mengedit Data

### Melalui Streamlit

1. Buka tab **Data**.
2. Edit nilai pada tabel.
3. Tambahkan atau hapus baris jika diperlukan.
4. Dashboard akan memvalidasi data dan menghitung ulang:
   - `rasio_ISPA_per_1000_balita`
   - `kategori_kayu_bakar`
5. Klik **Simpan perubahan ke CSV sumber**.

File berikut akan diperbarui:

```text
Dummy_Dataset_25Kolom_125Baris.csv
```

### Mengunggah Dataset Baru

Pada sidebar Streamlit:

1. Klik **Browse files** pada bagian **Ganti dataset (CSV)**.
2. Pilih file CSV.
3. Klik **Muat dataset pengganti**.

Dataset harus memiliki kolom wajib berikut:

```text
nama_kecamatan
nama_desa
jumlah_balita_0_59bln
kasus_ISPA_balita
persen_RT_kayu_bakar
```

Kolom lain tetap disarankan dipertahankan agar seluruh grafik dapat digunakan.

## Format Data

Data menggunakan format CSV dengan pemisah koma. Contoh header:

```csv
id_desa,kode_kecamatan,nama_kecamatan,nama_desa,tahun_data,jumlah_penduduk,jumlah_balita_0_59bln,kasus_ISPA_balita,persen_RT_kayu_bakar
```

Nilai berikut harus berupa angka:

- Jumlah penduduk
- Jumlah balita
- Jumlah kasus
- Persentase
- Jarak
- Ketinggian
- Luas wilayah
- Pendidikan
- Kepadatan penduduk

Rasio ISPA dihitung dengan rumus:

```text
rasio ISPA = kasus ISPA balita / jumlah balita × 1.000
```

Kategori kayu bakar dihitung dengan aturan:

```text
persen_RT_kayu_bakar >= 50  → Tinggi
persen_RT_kayu_bakar < 50   → Rendah
```

## Troubleshooting

### `streamlit` tidak dikenali

Pastikan virtual environment sudah aktif, kemudian jalankan:

```powershell
python -m pip install streamlit
python -m streamlit run dashboard_ispa.py
```

### `ModuleNotFoundError`

Pasang ulang dependensi:

```powershell
pip install streamlit plotly pandas numpy
```

### Dataset tidak ditemukan

Pastikan file berikut berada di folder yang sama dengan `dashboard_ispa.py`:

```text
Dummy_Dataset_25Kolom_125Baris.csv
```

### Port 8501 sudah digunakan

Jalankan Streamlit pada port lain:

```powershell
streamlit run dashboard_ispa.py --server.port 8502
```

Kemudian buka:

```text
http://localhost:8502
```

### Data tidak valid

Periksa bahwa:

- Header CSV sesuai.
- Kolom jumlah balita berisi angka.
- Kolom kasus ISPA berisi angka.
- Kolom persentase kayu bakar berisi angka.
- Tidak ada nama kolom wajib yang dihapus.

## Catatan

- Jangan menghapus file CSV sumber jika dashboard masih menggunakannya.
- Disarankan membuat salinan file CSV sebelum menyimpan perubahan besar.
- File `dashboard_ispa.html` dapat dibuat ulang kapan saja dengan menjalankan `python dashboard_ispa.py`.
- Untuk fitur edit dan penyimpanan langsung ke CSV, gunakan mode Streamlit.
