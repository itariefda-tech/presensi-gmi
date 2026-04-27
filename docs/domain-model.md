# Domain Model Definition

## 1. Core Concept: Site

Dalam sistem HRIS ini, istilah **Site** digunakan sebagai representasi utama unit kerja operasional dalam bisnis outsourcing.

### Definisi

**Site** adalah:
> Unit kerja spesifik milik seorang client yang menjadi lokasi penempatan tenaga kerja, memiliki konfigurasi operasional, aturan kerja, dan kebijakan yang dapat berbeda dengan site lainnya.

---

## 2. Karakteristik Site

Satu **Site** memiliki ciri-ciri berikut:

- Berada di bawah satu **Client**
- Merepresentasikan cabang, titik operasional, atau area kerja tertentu
- Memiliki:
  - aturan kerja (policy)
  - jadwal kerja (shift/schedule)
  - penempatan karyawan (assignment)
- Dapat memiliki konfigurasi berbeda walaupun masih dalam client yang sama

---

## 3. Relasi Antar Entitas

Relasi utama dalam sistem:

- **1 Client → memiliki banyak Site**
- **1 Site → memiliki banyak Employee**
- **1 Site → memiliki konfigurasi policy sendiri**
- **1 Site → memiliki jadwal kerja sendiri**

---

## 4. Catatan Penting

- Istilah **Site tidak selalu berarti lokasi fisik semata**
- Site juga merepresentasikan:
  - konteks operasional
  - aturan kerja
  - dan struktur penugasan

---

## 5. Konsistensi Terminologi

Untuk menjaga konsistensi sistem:

- Istilah `location` tidak digunakan lagi
- Semua referensi harus menggunakan istilah `site`
- Berlaku untuk:
  - database schema
  - backend logic
  - API
  - template (Jinja)
  - dokumentasi

---

## 6. Contoh Kasus

Client: Bank ABC

Memiliki beberapa Site:

- Site A: Cabang Bandung
  - Shift: 3 shift
  - Policy: standar bank

- Site B: Cabang Jakarta
  - Shift: 2 shift
  - Policy: khusus (jam operasional berbeda)

---

## 7. Tujuan Penggunaan Site

Penggunaan konsep Site bertujuan untuk:

- Mendukung fleksibilitas operasional
- Mengakomodasi perbedaan aturan antar cabang
- Mempermudah pengelolaan karyawan dan jadwal
- Menjadi dasar struktur data dalam sistem HRIS

---