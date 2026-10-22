# Arbiter — blueprint rombak UI/UX

**Status: proposal untuk persetujuan, bukan implementasi.** Scope: audit UI, perancangan information architecture, interaction dan roadmap. Source production, API, database dan staged changes pengguna tidak diubah. Nama produk yang benar: **Arbiter**.

## 1. Keputusan desain

**Primary surface: Operate / investigation desk.** Pertanyaan utama: “Alert mana yang perlu ditangani, apa buktinya, dan apa keputusan berikutnya?”

Arah yang direkomendasikan: **Quiet Evidence Desk**—empat destination yang jelas, antrean triage sebagai home, inspector kontekstual untuk eksplorasi cepat, halaman insiden untuk pekerjaan panjang. Bukan sekadar menambah sidebar yang men-scroll satu halaman yang sama.

Asumsi yang harus divalidasi saat implementasi: analis SOC menggunakan desktop untuk sesi panjang; mobile adalah akses review cepat, bukan authoring log intensif; local/offline menjadi constraint. Ini diinferensikan dari README dan source, bukan hasil user research.

### Alternatif yang dibandingkan

| Opsi | Komposisi | Kelebihan | Kekurangan / keputusan |
| --- | --- | --- | --- |
| Konservatif | Satu workbench, toolbar dibersihkan, drawer | Migrasi cepat; perubahan kecil | Ingest, report dan case authoring tetap tumpang tindih; tidak menyelesaikan permintaan modular sepenuhnya |
| **Strong fit — rekomendasi** | Triage / Insiden / Impor / Laporan, shared shell + inspector | Batas tugas jelas; recurring workflow cepat; bisa dimigrasikan bertahap | Perlu router, state contract dan scoped export yang konsisten |
| Divergen | Case-first workspace, queue menjadi Evidence inbox | Fokus investigasi mendalam | Analis harus punya case terlalu awal; kurang cocok untuk triage awal/ad-hoc |

Keputusan: opsi strong fit. Jangan campur komposisinya menjadi dashboard “Overview” berisi ringkasan semua halaman lagi.

## 2. Sitemap yang diusulkan

```text
Arbiter
├── Triage                       #/triage                 [default]
│   └── Alert inspector          #/triage?...&alert=<id>
├── Insiden                      #/incidents
│   └── Case workspace           #/incidents/<id>
│       ├── Ringkasan
│       ├── Bukti & kronologi
│       └── Analisis & rekomendasi
├── Impor                        #/imports
│   ├── File / Paste             [mode satu workflow]
│   └── Hasil impor sesi ini     [bukan history palsu]
└── Laporan                      #/reports?...scope
    ├── Scope + document preview
    └── Menu format              [GDocs, DOCX, XLSX, TSV, Markdown; CSV jika dipertahankan]

Utility: Status workspace, bantuan singkat, tenant switcher.
IP intelligence: context di inspector + explicit external pivot.
Correlation: panel kontekstual di Triage/Insiden, bukan duplicate app.
```

Hash routing adalah rekomendasi tahap awal agar deep link tidak memerlukan catch-all backend baru. Ini bukan route yang sudah tersedia. Clean URLs bisa ditambahkan nanti dengan routing FastAPI yang tidak menelan `/api/*` atau static files.

## 3. Apa yang boleh muncul di depan

### Triage default

- Title “Triage”, satu workspace/tenant scope, freshness yang jujur.
- Search, review status, tombol Filter, urutan, menu kolom.
- Default queue **Belum direview**; Semua dan Direview sebagai view sederhana. Review status tetap berbeda dari case status.
- Alert rows; satu action **Buka detail** per row atau label event sebagai button/link.
- Batch actions hanya saat selection ada.

### Dipindahkan dari depan

- Workflow strip permanen -> bantuan/first-run, bukan ruang di setiap kunjungan.
- Lima export/copy buttons -> Laporan dan satu contextual export entry.
- Form case panjang -> halaman insiden, quick-create hanya judul + metadata minimal.
- File/paste editor -> Impor.
- Full logs, raw JSON, duplicate instances -> inspector tabs.
- Correlation suggestions -> disclosure/panel saat diminta; tersedia tanpa menggeser seluruh antrean.
- Tenant tabs + tenant select -> satu switcher. Banyak tenant tidak menambah tinggi header.
- Table/Card toggle -> jangan dipertahankan sebagai dua renderer utama tanpa kebutuhan nyata; table desktop dan list mobile berbagi view model.

## 4. Wireframe dan first viewport

### A. Triage desktop

```text
┌─────────────────┬──────────────────────────────────────────────────────┐
│ Arbiter         │ Scope: [Tenant / Semua tenant]   Diperbarui … [Refresh]│
│                 ├──────────────────────────────────────────────────────┤
│ Triage          │ Triage                                  [Impor]      │
│ Insiden         │ Belum direview / Semua / Direview                    │
│ Impor           │ [Cari alert…] [Status] [Filter] [Urutan] [Kolom]      │
│ Laporan         ├──────────────────────────────────────────────────────┤
│                 │ □ Waktu  Severity  Event / asset  Source  Hits Review│
│                 │ □ …      …         …              …       …   …     │
│                 │ □ …      …         …              …       …   …     │
│                 │                                                      │
│ Status workspace│ [Jumlah aktual, rentang halaman]    [Prev] [Next]    │
└─────────────────┴──────────────────────────────────────────────────────┘
```

Inspector tertutup saat awal. Setelah alert dipilih pada desktop lebar, workspace menjadi queue + inspector. Jika lebar queue tidak cukup, gunakan detail region tunggal, bukan memaksa tabel sepuluh kolom.

```text
┌───────────────────────────────┬──────────────────────────────────┐
│ Antrean, filter tetap         │ Alert identity              [×]  │
│ selected row jelas            │ Severity · review · timestamp    │
│                               │ Rule + target + intel singkat     │
│                               │ [Detail] [Kejadian] [Raw]          │
│                               │ Bukti yang dipilih                │
│                               │ [Tandai direview] [Ke insiden]     │
└───────────────────────────────┴──────────────────────────────────┘
```

Back/Escape mengembalikan fokus ke row/trigger; filter, sort, pagination dan scroll tetap. Desktop inspector non-modal tidak mengunci page dengan blur/scrim. Mobile detail menggantikan list dan punya Back.

### B. Insiden index dan case workspace

```text
Insiden                                       [Buat insiden]
[Cari kasus…] [Status] [Severity]
Judul kasus                Status   Severity   Bukti   Diperbarui
…                          …        …          …       …

Insiden / <judul kasus>                        [Simpan] [Laporan]
Severity · status · scope yang diverifikasi
[Ringkasan] [Bukti & kronologi] [Analisis & rekomendasi]

Main editor / evidence timeline               Context rail
- ringkasan / technical analysis               - target assets
- conclusion                                  - rule / MITRE
- recommendation                              - linked alerts
```

Tidak ada grafik ornamental. Timeline adalah rangkaian kejadian dari actual evidence dengan first/last seen dan jumlah occurrence. Summary tidak menciptakan “composite risk score” yang backend belum punya.

### C. Impor

```text
Impor alert
[Upload file] [Tempel JSON]
[File picker / text editor yang lebar]
Format didukung + validation message
[Batal] [Impor alert]

Hasil sesi: parsed / inserted / deduplicated / warnings aktual
[Lihat hasil di Triage] [Impor lagi]
```

Tanpa persistent import batch ID, “Lihat hasil” hanya boleh mengarahkan ke scope yang tersedia dan menjelaskan batasnya. Jangan menyatakan hanya alert batch ini jika API belum bisa memfilternya. Preflight validation lokal tidak sama dengan transaksi server; jelaskan apakah dry-run tersedia. Jangan membuat determinate progress jika endpoint tidak melaporkan progress.

### D. Laporan

```text
Laporan
Scope: [Insiden / Alert terpilih / Query triage]
Tenant: …     Jumlah aktual: …     Batas/filter: …
[Preview dokumen]                                  [Ekspor ▾]
                                                  GDocs / DOCX / XLSX
                                                  TSV / Markdown
```

GDocs berarti copy rich HTML ke clipboard, bukan integrasi akun Google. CSV merupakan endpoint legacy tambahan di source; putuskan dipertahankan atau disembunyikan di format menu, bukan dihapus diam-diam.

### E. Mobile

```text
[Menu] Arbiter                           [Impor]
Triage
Scope: [Tenant ▾]
[Cari…]                         [Filter]
Belum direview / Semua
──────────────────────────────────────────────
Severity · event                       Hits
Asset · source · waktu              [Detail]
──────────────────────────────────────────────
```

Semua detail tetap reachable, tidak menjejalkan table desktop dalam viewport kecil. Selected mode dan Back tidak menghapus pekerjaan. Navigation destinations tetap halaman yang berbeda.

## 5. Information architecture & interaction contracts

### Scope

1. Tenant scope adalah context yang terlihat; bukan security boundary yang diasumsikan. Authorization/multi-tenant enforcement harus diverifikasi terpisah.
2. Pilih case tidak diam-diam mengganti tenant menjadi “all”. Jika case lintas tenant memang didukung, tampilkan label tersebut dan minta scope eksplisit; jika tidak, validasi case membership di server.
3. Selection disimpan per scope dan ID, bukan dibaca ulang dari checkbox DOM. Pindah tenant memberi pilihan clear/cancel bila selection ada.
4. “Pilih halaman ini” berbeda dari “Pilih semua hasil”. Yang kedua tidak boleh ditampilkan jika backend belum punya query-token/bulk model.
5. Report request berbagi satu scope serializer dengan query triage. Preview dan semua format harus mengarah ke dataset yang sama; count dan truncation harus eksplisit.

### Refresh

- Fetch memakai AbortController/request version, cek `response.ok`, schema dan error. Debounce tidak cukup untuk mencegah stale response menimpa query terbaru.
- Polling health tidak boleh menganggap jumlah record sama berarti isi/review/case tidak berubah.
- Poll tidak menghapus selection, edit draft, expanded occurrence, atau focused control. Data baru dapat diantrekan sebagai notice; revalidation ketika visible/tab aktif.
- Status “terhubung” hanya setelah verifikasi sukses; perlihatkan stale/offline/error dan last successful refresh.

### Editing dan destructive actions

- Case editor punya explicit Save, pending/error/saved, dirty guard, retry tanpa hilang input. Satu save model per view.
- Quick review bisa optimistic hanya jika rollback jelas. Undo jangan ditawarkan jika tidak ada real reversal contract.
- Delete case confirmation menyebut judul dan konsekuensi; jangan menyiratkan alert ikut dihapus jika backend tidak begitu.
- Clipboard failures mempertahankan scope ketika fallback; raw copy diberi label sensitif. Redaction tidak menjamin aman untuk cloud.

### Accessibility

- `<nav>`, `<main>`, satu page `<h1>`, skip link, `aria-current` untuk navigation.
- Button untuk action, link untuk route. Filter chips button/pressed state; sort button di `<th>` + `aria-sort`.
- Label `for`/id untuk setiap input; checkbox accessible name dan mixed-state master checkbox.
- Focus-visible 2px yang kontras, tidak terpotong sticky region. Drawer/menus/dialog mengikuti keyboard model yang tepat.
- Async status `aria-live="polite"`; validation inline + focus error; no color-only status.

## 6. Arsitektur module yang disarankan

Pertahankan **FastAPI + HTML/CSS + native JavaScript ES modules**. Source yang dibaca tidak memakai React atau build pipeline frontend. README menyebut Tailwind, tetapi `app/index.html` memakai inline CSS; jangan migrasi framework/library untuk menyelesaikan clutter.

```text
app/
├── index.html                  # shell + entry module, tidak semua UI
├── static/
│   ├── styles/
│   │   ├── tokens.css
│   │   ├── base.css
│   │   ├── shell.css
│   │   └── components.css
│   ├── js/
│   │   ├── app.js
│   │   ├── router.js
│   │   ├── api/client.js        # timeout, response.ok, error schema
│   │   ├── api/alerts.js
│   │   ├── api/incidents.js
│   │   ├── api/imports.js
│   │   ├── api/reports.js
│   │   ├── state/workspace.js
│   │   ├── state/selection.js
│   │   ├── state/triage.js
│   │   ├── features/triage/     # view, table/list, inspector, filters
│   │   ├── features/incidents/  # list, editor, evidence timeline
│   │   ├── features/imports/    # upload/paste, result states
│   │   ├── features/reports/    # scope, preview, export
│   │   └── ui/                 # button, menu, status, dialog, drawer
│   └── fonts/                  # verified local assets + license
└── main.py                     # static mount + existing APIs
```

Ini target file tree, bukan file yang sudah ditulis. Tambahkan StaticFiles mount pada implementasi; jaga current `/api/*`, MIME, cache policy, dan Docker bind-mounted `app/` yang saat review terdeteksi. Native JS cukup; TypeScript hanya jika diputuskan terpisah bersama build tooling, bukan kewajiban dari proyek Damsel & Desire.

Module harus punya init/dispose dan melepas event listeners, timers dan pending request saat route berubah. Router tidak membawa semua feature listener global. Template render meng-escape text dan menghindari inline `onclick` untuk dynamic payload.

### State model

- URL: page, tenant, q, review_status, filter_preset, sort_by, sort, offset/limit, alert/case identity.
- Transient memory: selected IDs per scope, active inspector tab, scroll-restoration map, request state.
- Drafts: default memory session; penyimpanan durable narrative membutuhkan keputusan privacy dan storage terpisah.
- Local preference boleh menyimpan density/column IDs; **bukan raw alert, IP, log, token atau case narrative**.

## 7. Kesiapan backend: pakai yang ada vs perlu kerja

| Area | Contract yang sudah ada di source | Gap untuk experience yang diusulkan |
| --- | --- | --- |
| Triage | `GET /api/alerts`, q/tenant/review/filter/sort/limit/offset, total | Lightweight summary vs heavy raw response; detail endpoint; stable paging; selection contract; scope tetap tenant-safe saat group_id |
| Review | Per-alert PUT dan batch-review POST | Error/rollback; update version/freshness, validation/authorization ditinjau terpisah |
| Insiden | CRUD `/api/groups`, membership endpoints | Scoped list/detail, actual case metadata, counts dan boundaries; editor dirty handling di frontend |
| Correlation | `/api/suggestions` | Saat ini global latest 300 pada source; perlu tenant/query scope sebelum ditampilkan sebagai saran scoped |
| Impor | `/api/import`, `/api/import-text`, parsed/inserted/deduplicated/warnings | Tidak ada batch history/dry-run/progress contract yang terbukti; fitur tersebut backlog, jangan palsukan |
| Laporan | report-html/docx/xlsx/tsv/markdown, CSV legacy; tenant/group/IDs | Shared query scope; preview identity/count; no silent 500-row fallback; fallback clipboard harus mempertahankan scope |
| Intel | Joined cache fields + external IP dashboard pivot | Summary/detail/freshness, unknown vs zero detection semantics; jangan membangun intelligence database browser baru tanpa kebutuhan |
| Status | `/api/health` count totals | Freshness signal yang mencerminkan updates, bukan hanya count; offline state jujur |

Graphify membantu memetakan Python dependency; query yang dipakai tidak menampilkan fungsi JS dari HTML. Frontend behavior dikonfirmasi dari source dan isolated render, bukan diasumsikan tercakup graph.

## 8. Roadmap implementasi, tiap tahap bisa diverifikasi

### Phase 0 — safety & baseline

- Catat current behavior dan staged changes; jangan overwrite pekerjaan pengguna.
- Buat sanitized/synthetic browser fixtures yang jelas terpisah dari production; tidak mengakses database sensitif.
- Capture baseline 1440/1280, 768, 390 dan 320px; keyboard journey; export scope tests.
- Tentukan mapping severity dan semantics review vs case status bersama backend.
- Gate: fixture network hanya localhost review; tidak ada production data atau third-party request.

### Phase 1 — modular foundation + shell

- Extract CSS, JS dan API client tanpa perubahan business logic; buat router, lifecycle dan typed-by-contract view models.
- Shared shell + empat destination; one tenant switcher; menu/focus primitives.
- Gate: deep link, Back/Forward, reload, empty/error/unknown route dan offline; tidak ada regression route/API lama.

### Phase 2 — triage-first experience

- Queue toolbar ringkas, column priority, pagination, inspector, dedicated selection store.
- Stabilkan search/refresh; unknown intel bukan clean; batch tidak menutupi konten.
- Gate: shift-range + select page + batch review, tenant switch, pending refresh, 200% zoom, keyboard-only, long data. Tabel/list muncul cepat tanpa hero.

### Phase 3 — insiden workspace

- List kasus, quick-create, halaman detail, evidence timeline dan long-form editor.
- Correlation panel memakai scope nyata; link evidence kembali ke Triage dengan context.
- Gate: save/error/dirty guard, membership, cross-tenant behavior, delete semantics, no lost input.

### Phase 4 — impor dan laporan

- File/paste unified import; validasi + actual server result.
- Scope selector, report preview, satu format menu; semua export memakai same scope contract.
- Gate: malformed/empty/large import, duplicate IDs, invalid encoding, clipboard denied, export >500, tenant+case+selection consistency. Tidak ada truncation tak tertera.

### Phase 5 — hardening & rollout

- Self-host fonts/assets; runtime no external requests; CSS token sweep secondary states.
- Browser tests di 320/375/390/414/768/1280/1440px; focus visibility, reduced motion, screen reader spot checks, long content.
- Run unit/backend tests hanya pada disposable test database yang eksplisit. **Jangan menjalankan integration suite ke database SGU aktif.**
- Gate: no page overflow, no inaccessible action, no mixed legacy neon, no console error; all named workflows retain behavior.
- Release bertahap dengan feature flag/branch dan rollback; jangan hapus UI lama sebelum acceptance.

## 9. Acceptance checklist

- [ ] Empat destination benar-benar berganti view dan punya URL; bukan anchors pada halaman panjang.
- [ ] Triage default tidak menampilkan report/import/case editor sekaligus.
- [ ] First row <=240px pada 1440×900 dan <=280px pada 1280×720.
- [ ] One tenant switcher; query, selected IDs dan case context tidak berubah diam-diam.
- [ ] Inspector retains filters, selection, scroll and focus; mobile Back kembali utuh.
- [ ] No live database content used in demo artifacts or external resources.
- [ ] Offline, empty, no-match, loading, stale, partial error dibedakan.
- [ ] All export formats and clipboard fallback use identical explicit scope; no silent cap.
- [ ] Keyboard sortable headers, labelled controls, visible focus, live async feedback.
- [ ] No page overflow at named widths; 44px mobile targets; 200% zoom usable.
- [ ] Production CSS/JS split into domain modules with disposal and shared API client.
- [ ] Font/assets self-hosted; no runtime CDN dependency.

## 10. Open decisions sebelum build

1. Konfirmasi **Quiet Evidence Desk + empat destination**; alternatif disimpan untuk diskusi, bukan ketiganya dibangun.
2. Validasi apakah case boleh lintas tenant; jangan menebak security policy.
3. Tentukan scope contract export query dan detail endpoint sebelum report builder.
4. Setujui interface copy Indonesia dengan technical names konsisten; source saat ini campuran.
5. Tentukan kebutuhan persistent import history, drafts, permissions, saved views; semuanya backlog jika tidak didukung contract.

Tidak ada estimasi hari yang diklaim tanpa mengetahui kapasitas tim. Urutan di atas sengaja berdasarkan dependency dan risiko, bukan janji waktu.
