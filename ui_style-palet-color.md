# UI Style Palet Color

## Tujuan

Dokumen ini dipakai sebagai acuan rasa warna default untuk dashboard admin, agar tampilan tetap konsisten, tenang, modern, dan tidak melelahkan saat dipakai membaca data dalam durasi lama.

## Karakter Umum

Palet warna UI yang dipakai harus terasa:

- calm
- bersih
- profesional
- modern
- tidak terlalu ramai
- tidak terlalu kontras keras

Hindari palet yang terasa:

- terlalu jingga menyala
- terlalu ungu dominan
- terlalu coklat / beige
- terlalu gelap pekat tanpa layer
- terlalu putih polos tanpa kedalaman

## Default Panel/Card

### Tema Dark

Background panel/card default pada mode gelap harus terasa seperti:

- dark calm
- slate
- charcoal
- blue-gray
- glass dark tipis

Ciri visual:

- dasar warna gelap lembut, bukan hitam pekat
- ada layer transparansi ringan
- border tipis transparan
- shadow halus
- isi konten lebih menonjol daripada wadahnya

Rasa warna yang disarankan:

- background: `rgba(255,255,255,0.02 - 0.05)` di atas base gelap
- border: `rgba(255,255,255,0.08 - 0.14)`
- shadow: `rgba(0,0,0,0.08 - 0.18)`

### Tema Light

Background panel/card default pada mode terang harus terasa seperti:

- light calm
- bright sky blue di bagian atas
- soft medium blue di bagian tengah
- warm sand / beige lembut di bagian bawah
- terasa seperti panel gradien khas dashboard admin
- bukan panel flat satu warna

Ciri visual:

- panel/card memakai gradasi beberapa warna
- bagian atas terasa lebih cerah dan segar
- bagian tengah tetap biru agar ritme dinginnya terjaga
- bagian bawah turun ke warna hangat lembut supaya tidak terasa terlalu dingin
- hasil akhirnya terasa manusiawi, tenang, dan khas
- ini adalah default card light utama dashboard admin

Rasa warna yang disarankan:

- gradient utama default:
  - atas: `#d7e9ff`
  - tengah: `#bcd8f6`
  - bawah: `#f0dfc7`
- bentuk CSS aslinya:
  - `linear-gradient(180deg, #d7e9ff 0%, #bcd8f6 55%, #f0dfc7 100%)`
- nama rasa visual:
  - sky blue
  - powder blue
  - warm sand
- border umum: `rgba(15,23,42,0.12 - 0.18)`
- shadow: `rgba(15,23,42,0.08 - 0.14)`

Catatan sumber:

- gradient ini terdefinisi di `static/css/dashboard.css`
- token yang dipakai adalah `--card-light`
- lalu dipakai oleh `html[data-theme="light"] .card`

## Accent Default

Accent dipakai untuk:

- icon dekoratif
- tombol aktif
- highlight tab
- badge penting
- progress visual

Accent utama yang aman:

- sky blue
- cyan lembut
- teal dingin
- indigo ringan
- violet secukupnya

Hindari accent yang terlalu dominan jika dipakai banyak sekaligus.

## Warna yang Disukai untuk Aksen

### Biru Langit Calm

Cocok untuk:

- highlight utama
- icon dekoratif
- status aktif yang halus
- card tema biru terang

Contoh rasa:

- `#38bdf8`
- `#0ea5e9`
- `#7dd3fc`

### Teal Calm

Cocok untuk:

- operasional aktif
- progress baik
- KPI yang ingin terasa segar

Contoh rasa:

- `#14b8a6`
- `#0f766e`
- `#2dd4bf`

### Indigo / Violet Terkontrol

Cocok untuk:

- analitik
- highlight kategori
- panel modern yang tetap elegan

Contoh rasa:

- `#6366f1`
- `#8b5cf6`
- `#7c3aed`

Gunakan secukupnya agar UI tidak terasa terlalu ungu.

### Kuning Calm

Kuning dipakai hanya sebagai aksen khusus, bukan warna dominan utama.

Cocok untuk:

- icon tertentu
- penanda jumlah / project
- perhatian ringan

Contoh rasa:

- `#facc15`
- `#f5d76e`
- `#fde68a`

Hindari kuning yang terlalu tajam atau neon.

## Warna yang Perlu Diredam

Gunakan dengan hati-hati:

- orange terang
- jingga menyala
- pink terlalu panas
- ungu terlalu dominan

Jika warna tersebut dipakai, sebaiknya diarahkan ke versi:

- lebih dingin
- lebih lembut
- lebih pudar
- lebih sedikit porsinya

## Ringkasan Praktis

Jika ragu, gunakan arah berikut:

- panel dark: slate gelap transparan
- panel light: gradien biru terang -> biru lembut -> beige hangat
- accent utama: biru langit calm
- accent sekunder: teal, indigo, violet secukupnya
- accent khusus: kuning calm

## Ringkasan Satu Kalimat

Palet warna UI admin harus terasa tenang dan khas, dengan default panel light berbentuk gradien biru terang ke biru lembut lalu turun ke beige hangat, serta aksen biru-langit sebagai pusat identitas visual utama.
