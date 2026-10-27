# Standar Operasional Prosedur (SOP) Autonomous Engineering & Rigor

Dokumen ini adalah **aturan operasional wajib** untuk seluruh model AI (Gemini, Claude, GPT, Antigravity, Codex) dan seluruh sesi pengerjaan pada repositori Arbiter.

---

## 🎯 Filosofi Inti: "No Stubs, Full Seam, Zero Hallucination"

Tidak ada toleransi untuk:
1. **Fitur Pajangan (Decorative Stubs):** Menampilkan tombol, opsi dropdown, atau grafik yang tidak tersambung utuh sampai ke backend dan database.
2. **Klaim Selesai Sembrono:** Mengklaim "100% selesai" hanya karena unit test buatan sendiri lolos, tanpa memverifikasi sambungan integrasi ujung-ke-ujung (*end-to-end seam*).
3. **Penyakit Menunggu Diperintah:** Menunggu user meminta dibuatkan checklist atau disuruh pakai skill. Agent wajib berinisiatif secara otomatis sejak belokan pertama.

---

## 📋 Protokol Eksekusi Wajib

### 1. Inisialisasi Task Otomatis (`todo_list`)
- Setiap kali menerima tugas rekayasa perangkat lunak multi-langkah (3 langkah atau lebih) atau lintas modul (UI + API + DB):
  - **Wajib langsung menginisialisasi `todo_list`** di respon pertama tanpa disuruh.
  - Perbarui status tugas secara berkala (`in_progress` saat aktif, `completed` hanya jika sudah terverifikasi bukti eksekusi nyata).

### 2. Proaktif Menggunakan Skills & Subagents
- **Jangan pernah menebak alur kerja.** Langsung panggil skill yang relevan:
  - `subagent-driven-development`: Delegasikan subtugas independen ke subagent terisolasi dengan review dua tahap (kepatuhan spek & kualitas kode).
  - `test-driven-development`: Tulis regression test yang gagal (*RED*) terlebih dahulu sebelum mengubah kode produksi, lalu perbaiki (*GREEN*).
  - `systematic-debugging`: Investigasi akar masalah (reproduksi -> inspeksi data riil -> isolasi -> perbaikan permanen).
  - `requesting-code-review`: Audit perubahan sebelum di-commit.

### 3. Pelacakan Jahitan Data Ujung-ke-Ujung (*Trace Every Seam*)
Setiap fitur baru atau filter data wajib diverifikasi melewati 8 lapisan jahitan data tanpa ada yang terputus:
1. **Frontend DOM:** Input form / event listener terdaftar dengan benar.
2. **State & Router:** Parameter tersimpan di URL hash / query string dengan tipe data yang tepat.
3. **API Client Fetch:** Parameter dikonversi ke `URLSearchParams` dan dikirim via HTTP request.
4. **Backend Route Signature:** Endpoint FastAPI (misal `@app.get("/api/...")`) **wajib secara eksplisit mendeklarasikan parameter tersebut**. Parameter yang tidak dideklarasikan akan dibuang secara diam-diam oleh FastAPI!
5. **SQL Query Builder:** Parameter dipetakan ke klausul `WHERE`, `GROUP BY`, atau `ORDER BY` dengan prepared statement (`%s`).
6. **Eksekusi Database:** Indeks dan tipe data cocok, tidak ada query lambat atau table scan tak perlu.
7. **Response Payload:** Skema JSON yang dikembalikan mencakup data yang dibutuhkan frontend.
8. **Render UI & Aksesibilitas:** DOM menampilkan data secara akurat, responsif, dan menyertakan state kosong/error.

### 4. Pengujian Kasus Negatif (Bukan Cuma Kasus Ideal)
- Jangan hanya menguji apakah data yang dicari muncul.
- **Wajib menguji apakah data yang TIDAK sesuai benar-benar tereliminasi.**
  - Contoh: Filter `facet=Suspicious URL access` harus membuktikan bahwa alert `Web server 400 error` terbuang 100% dari hasil.
  - Contoh: Filter `time_preset=24h` harus membuktikan bahwa alert lebih dari 24 jam lalu tidak ikut terambil.

### 5. Verifikasi Lingkungan & Container
- Sadari bahwa Uvicorn di dalam kontainer Docker produksi mungkin tidak memakai `--reload`.
- Setiap kali ada penambahan endpoint baru atau perubahan skema SQL:
  - Jalankan test suite lokal (`node --test`, `unittest`).
  - Lakukan restart container (`docker restart arbiter`) bila diperlukan agar perubahan termuat di proses server.
  - Verifikasi output nyata via test client atau curl sebelum melaporkan ke user.
