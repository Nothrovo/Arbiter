# Standar Operasional Prosedur (SOP) Autonomous Engineering & Rigor

Dokumen ini adalah **aturan operasional wajib** untuk seluruh model AI (Gemini, Claude, GPT, Antigravity, Codex, Hermes Agent) dan seluruh sesi pengerjaan pada repositori Arbiter dan ekosistem terkait.

---

## ⚡ Mode Eksekusi: Slash Command `/work` vs Normal Prompt

### 1. Mode Maksimal (`/work`) — Autonomous Deep Engineering Mode
Ketika prompt pengguna diawali atau mengandung perintah `/work` (misal: `/work buat fitur X`, `/work investigasi alert Y`, atau sekadar `/work`):
- **Wajib Bekerja Secara Maksimal (Full Rigor):** Seluruh ketentuan dalam SOP ini wajib dijalankan 100% tanpa kompromi dan tanpa jalan pintas.
- **Orkestrasi Multi-Skill (Minimal 3–5 Skills):**
  - Agent **wajib secara proaktif memuat dan menerapkan minimal 3 hingga 5 skill yang relevan** dengan tugas yang diberikan.
  - Contoh kombinasi skill:
    - *Arsitektur & Rencana:* `writing-plans` / `api-design-principles` / `architecture-diagram`
    - *Delegasi & Eksekusi:* `subagent-driven-development` / `autonomous-ai-agents`
    - *Pengujian & Rigor:* `test-driven-development` (RED-GREEN-REFACTOR)
    - *Investigasi Akar Masalah:* `systematic-debugging`
    - *Audit & Kualitas:* `requesting-code-review` / skill domain (misal: `siem-alert-analysis`)
- **Proactive Skill Sourcing & Discovery:**
  - Jika belum ada skill lokal yang pas untuk domain tugas:
    - Agent **wajib mencari skill** di catalog/hub (`manage_catalog`, `tool_search`, atau katalog resmi), atau
    - Menyusun/membuat panduan skill terstruktur baru via `skill_manage` sebelum melangkah ke implementasi kode.
    - **Dilarang keras menebak atau menulis kode spekulatif tanpa panduan skill.**
- **Inisialisasi `todo_list` Otomatis di Turn Pertama:**
  - Langsung inisialisasi daftar tugas terstruktur di respon pertama tanpa menunggu instruksi checklist dari user.
  - Perbarui status tugas secara aktif (`in_progress` saat dikerjakan, `completed` hanya jika sudah terbukti lewat eksekusi riil).
- **Delegasi Subagent & Paralelisasi Task (`delegate_task`):**
  - Pecah tugas multi-langkah ke dalam subagent independen terisolasi.
  - Terapkan evaluasi dua tahap: evaluasi kepatuhan spesifikasi (*spec compliance*) dan evaluasi kualitas kode (*code quality review*).
- **Pelacakan 8 Lapisan Jahitan Data (*Trace Every Seam*):**
  - Pastikan setiap parameter dan komponen tersambung utuh dari UI DOM sampai basis data.
- **Pengujian Kasus Negatif & Verifikasi Nyata:**
  - Uji eliminasi data yang tidak sesuai dan buktikan pada container/service yang berjalan nyata.

### 2. Mode Normal (Tanpa `/work`)
- Usaha, kedalaman, dan format jawaban disesuaikan secara proporsional dengan bobot prompt pengguna tanpa overhead multi-agent berlebihan.

---

## 🎯 Filosofi Inti: "No Stubs, Full Seam, Zero Hallucination"

Tidak ada toleransi untuk:
1. **Fitur Pajangan (Decorative Stubs):** Menampilkan tombol, opsi dropdown, atau grafik yang tidak tersambung utuh sampai ke backend dan database.
2. **Klaim Selesai Sembrono:** Mengklaim "100% selesai" hanya karena unit test buatan sendiri lolos, tanpa memverifikasi sambungan integrasi ujung-ke-ujung (*end-to-end seam*).
3. **Penyakit Menunggu Diperintah:** Menunggu user meminta dibuatkan checklist atau disuruh pakai skill. Agent wajib berinisiatif secara otomatis sejak belokan pertama saat `/work` aktif.

---

## 📋 Protokol Eksekusi Rinci

### 1. Inisialisasi Task Otomatis (`todo_list`)
- Setiap kali menerima tugas rekayasa perangkat lunak multi-langkah (3 langkah atau lebih) atau lintas modul (UI + API + DB):
  - **Wajib langsung menginisialisasi `todo_list`** di respon pertama tanpa disuruh.
  - Perbarui status tugas secara berkala (`in_progress` saat aktif, `completed` hanya jika sudah terverifikasi bukti eksekusi nyata).

### 2. Proaktif Menggunakan Skills & Subagents
- **Jangan pernah menebak alur kerja.** Langsung panggil minimal 3-5 skill yang relevan:
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

### 6. Anti-Pengerdilan Data (Zero Artificial Truncation)
- Jangan pernah menggabungkan kategori frekuensi rendah ke dalam wadah "Lainnya" / "Other" tanpa izin pengguna.
- Dalam telemetri keamanan, alert dengan kemunculan tunggal (seperti 1 probe SQLi atau kebocoran kredensial) kerap kali merupakan indikator serangan paling krusial. Tampilkan setiap kategori unik secara terpisah.

### 7. Dual-Heuristic Spotter & Proporsi Real-Time
- Sediakan tombol seleksi otomatis *Malicious Spotter* (mendeteksi probe sensitif: `.env`, `.git`, `.ssh`, webshell, path traversal, exploit query) dan *Benign Spotter* (memilih pola rutin non-berbahaya).
- Selalu hitung dan tampilkan proporsi/persentase alert terpilih terhadap total induk baik pada toast maupun toolbar pemilihan (`X sub-kategori dipilih (Y alert · Z%)`).

### 8. Aksi Langsung pada Tabel Luar (Outer-View Direct Actions)
- Pada daftar kasus atau entitas, sediakan pemicu aksi langsung (misal: tombol hapus dengan konfirmasi aman) pada baris tabel terluar. Jangan memaksa analis membuka halaman detail hanya untuk tindakan rutin.
