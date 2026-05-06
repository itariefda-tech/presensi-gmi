# UI Style Table Default

## Tujuan

Style tabel ini dipakai untuk menjaga tampilan tabel admin tetap rapi, padat, mudah dibaca, dan tidak saling dorong atau bertabrakan saat isi data banyak atau saat layar menyempit.

## Prinsip Utama

1. Beberapa kolom boleh digabung menjadi 1 sel jika datanya masih seritme.
2. Dalam 1 sel, data ditampilkan secara vertikal atas-bawah, bukan rapat horizontal.
3. Baris atas adalah informasi utama dan boleh `bold`.
4. Baris bawah adalah informasi pendukung dan tidak `bold`.
5. Header kolom mengikuti pola yang sama: judul utama di atas, subjudul di bawah.
6. Jangan ada pengulangan nama label kolom di setiap output sel jika header sudah cukup jelas.
7. Lebar kolom harus diatur proporsional sesuai isi, agar tidak saling mendorong.
8. Kolom yang berisi teks panjang seperti alamat, alasan, keterangan, atau catatan harus diberi ruang lebih lebar.
9. Kolom aksi sebaiknya tetap berdiri sendiri jika tombol membutuhkan ruang interaksi.
10. Hasil akhir harus terasa manusiawi dibaca, cepat discan, dan stabil secara visual.

## Notice Penting

- Hindari menulis ulang label seperti `Nama`, `Email`, `Status`, `Tanggal`, dan sejenisnya di dalam setiap sel output jika label tersebut sudah tampil di header kolom.
- Pengulangan label di isi sel membuat tabel terasa penuh, bising, dan tidak efisien dibaca.
- Pengecualian hanya dipakai jika tabel tampil tanpa header yang jelas atau saat konteks data benar-benar bisa membingungkan tanpa penanda tambahan.

## Pola Layout

### Header

- Judul utama di atas
- Subjudul di bawah
- Subjudul lebih ringan secara visual

Contoh:

- `Nama` di atas
- `Email` di bawah

### Isi Sel

- Value utama di atas
- Value pendukung di bawah
- Value atas `bold`
- Value bawah `normal`

Contoh:

- `Budi Santoso`
- `budi@company.com`

## Aturan Penggabungan Kolom

Gabungkan kolom jika:

- dua data masih saling terkait
- digabung justru membuat tabel lebih ringkas
- tidak mengurangi keterbacaan

Contoh pasangan yang baik:

- `Nama / Email`
- `Tanggal / Metode`
- `Check-in / Check-out`
- `Client / Site`
- `Status / Keterangan`

Hindari penggabungan jika:

- data aksi butuh ruang sendiri
- data terlalu panjang dan membuat 1 sel terlalu berat
- dua data tidak punya hubungan ritme baca

## Aturan Lebar Kolom

- Gunakan lebar kolom yang terkontrol
- Usahakan tabel tidak liar mengikuti isi terpanjang
- Gunakan pendekatan proporsional
- Terapkan kolom paling lebar untuk data panjang
- Gunakan `table-layout: fixed` bila diperlukan untuk menjaga stabilitas

## Target Visual

Style tabel ini harus menghasilkan tampilan yang:

- tidak tabrakan
- tidak dorong mendorong
- tidak terasa penuh sesak
- tetap padat informasi
- mudah dibaca cepat
- konsisten dengan ritme tabel payroll

## Ringkasan Satu Kalimat

Ini adalah pola tabel administratif dengan pasangan data atas-bawah dalam satu sel, memakai hierarki visual yang jelas dan lebar kolom terkontrol agar stabil, rapi, dan tidak bertabrakan.
