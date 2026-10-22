# Arbiter — audit UI/UX dan keputusan redesign

Method: dual-agent (A: sa-0-11fc1fa3 · B: sa-1-4223871c), disintesis dan diperiksa ulang oleh Luna.

**Status: review selesai; redesign belum diimplementasikan.** Produk yang benar adalah Arbiter. Tidak ada production source, API atau database yang diubah. Perubahan staged pengguna tetap dibiarkan.

## Ringkasan

Arbiter bukan generic SaaS tanpa domain: Wazuh rules, dedup occurrences, first/last seen, tenant/agent, MITRE, incident narrative dan local intel menunjukkan product truth yang kuat. Yang buruk adalah bagaimana seluruh pekerjaan ditumpuk dalam satu layar dan bagaimana state/scope dipertahankan.

**Design health: 19/40**, penilaian heuristik reviewer, bukan hasil usability study atau benchmark otomatis. Perombakan harus dimulai dari information architecture dan interaction contracts, baru visual polish.

Rekomendasi: **Quiet Evidence Desk** dengan empat destination: **Triage, Insiden, Impor, Laporan**. Triage menjadi home; detail cepat berada di inspector kontekstual; authoring panjang di case workspace. Jangan menambah halaman Overview yang menumpuk ringkasan semua fitur lagi.

## Metode dan batas bukti

- Graphify query dijalankan sebelum source exploration setelah graph tersedia; API relationships dikonfirmasi lewat graph/path. Graph query tidak cukup meliput JavaScript di HTML, sehingga frontend diperiksa langsung pada file yang sudah ditemukan.
- Source: `app/index.html:1–1490`; `app/main.py:127–243,281–397,400–537`; README. Satu HTML mengandung CSS, shell, semua modal, renderer dan handlers; ada 56 inline onclick dan tidak ada CSS @media pada source yang diaudit.
- Browser: isolated static copy dengan empty fixture dan fetch shim; **tidak mengakses database rows, .env, actual API records, log asli, atau production port 8000**. Font eksternal diblokir.
- Desktop screenshot dilihat; mobile screenshot reviewer juga diperiksa ulang. Modal/keyboard, URL state, health failure dan clipboard rejection diuji hanya pada fixture.
- Populated rows, real imports, actual case writes, exports, authorization, performance pada volume nyata, browser engine lain dan physical touch devices **belum diuji**. Temuan ekspor/selection pada data nyata adalah risiko berbasis source, bukan insiden kebocoran yang dibuktikan.
- Fixture menambah banner review: 31px desktop, 46px pada 390px, 61px pada 320px. Font fallback dan mode emulation membuat koordinat mobile antar-capture sedikit berbeda; jangan memperlakukan satu angka sebagai production benchmark.

## Bukti komposisi dan responsive

| Capture | Posisi tabel | Lebar dokumen | Interpretasi |
| --- | --- | --- | --- |
| Parent 1280×577 | y395, termasuk banner 31px | 1265px body dalam viewport 1280px | 24 control sebelum tabel; hitungan ini mengecualikan sort headers dan master checkbox |
| Parent 1440×900 | y395 | 1440px | Kontrol mengambil porsi besar first viewport bahkan saat kosong |
| Parent 768×1024 | y502 | 768px | Control stack bertambah tinggi |
| Parent 390×844 | y941, termasuk banner yang wrap | 443px | Horizontal page overflow; hasil di bawah fold |
| Reviewer B 390×844 mobile emulation | y921.5; y875.5 tanpa banner | 443px | Temuan overflow dan displacement terkonfirmasi, exact y dipengaruhi capture mode |
| Parent 320×780 | y1062 | 443px | Layout tidak beradaptasi untuk narrow screen |

Angka 28 yang sempat disebut dalam chat merupakan query selector lebih luas yang mencakup affordance tabel. Angka yang dipakai untuk **control sebelum tabel** adalah 24 pada parent capture. Reviewer B memakai definisi click targets lebih luas dan menghitung 30 pada keseluruhan empty UI; kedua angka tidak boleh dijumlahkan atau disamakan.

## Nielsen heuristics

Skala: 0 tidak tersedia/buruk, 4 sangat baik. Semua heuristik berlaku pada operational app ini.

| Heuristik | Skor | Bukti utama |
| --- | ---: | --- |
| Visibility of system status | 2/4 | Result count ada; Live Sync statis dan health failure ditelan (`index.html:287,667–678`) |
| Match system / real world | 3/4 | Domain SOC kuat; reviewed/selesai/pending ambigu (`:355–359,934–936`) |
| User control and freedom | 2/4 | Batal/reverse review ada; Escape ingest gagal, reset filter lengkap tidak tersedia |
| Consistency and standards | 2/4 | Tenant tab+select duplikat; report dianggap view setara table; export scope berbeda |
| Error prevention | 2/4 | JSON preview dan title validation ada; scope export dan klaim redaksi belum aman |
| Recognition rather than recall | 2/4 | Workflow strip membantu, tetapi case context dan selection scope harus diingat |
| Flexibility and efficiency | 2/4 | Batch/shift-click tersedia; selection melekat ke DOM tabel |
| Aesthetic and minimalist design | 2/4 | Dark base cocok; control untuk semua fase bersaing di atas queue |
| Error recovery | 1/4 | Error text/alert generik, kurang retry dan pemulihan kontekstual |
| Help and documentation | 1/4 | Strip empat langkah tidak menjelaskan severity, scope atau batas redaksi |
| **Total** | **19/40** | **Perlu redesign UX, bukan recolor** |

## Yang layak dipertahankan

1. Struktur informasi SOC: waktu, severity, rule, target, source intel dan review yang dekat dengan bukti (`index.html:394–409,870–954`).
2. Dedup dengan occurrences dan first/last seen: mengurangi repetisi tanpa menghilangkan kronologi (`:900–917,1211–1224`).
3. Batch selection dan incident narrative yang memuat analisis, verdict serta rekomendasi (`:438–445,597–607,1015–1027`).

## Prioritas — Before / After / Why

| Priority | Before | After | Why |
| --- | --- | --- | --- |
| **P1 · correctness/privacy** | DOCX/XLSX link tanpa filter; clipboard format membawa scope berbeda (`index.html:374–375,1416–1477`; `main.py:400–458`) | Satu ExportScope untuk selected IDs / case / query; preview tenant+count+limit sebelum semua format | Output bisa berbeda dari konteks yang analis kira sedang diekspor. Perbaiki contract, bukan hanya sembunyikan tombol |
| **P1 · structure** | Ingest, filter, selection, korelasi, report dan case modal bercampur (`:296–617`) | Empat route, queue sebagai home, inspector kontekstual, case editor dedicated | Memisahkan pekerjaan tanpa menggandakan tightly coupled triage |
| **P1 · state/trust** | Selection dibaca dari checkbox DOM; reload merender ulang; Live Sync tetap hijau; clipboard success tanpa await (`:667–678,1035–1042,1283–1321`) | selectedIds store per scope; refresh aman; connection state nyata; tunggu clipboard berhasil | Kecepatan tidak berguna jika pilihan dan status tidak dipercaya |
| **P1 · access** | Span onclick / clickable th, modal tanpa focus lifecycle, labels tidak terhubung (`:331–340,401–403,449–617,1104–1106`) | Semantic controls, aria-sort, labels, dialog/inspector keyboard model, Escape dan focus restore | Analis keyboard dan assistive tech harus mendapat operasi setara |
| **P1 · responsive** | Tidak ada @media; page 443px pada viewport 390/320px (`:46–66,81–85,178,231`) | Folded nav/filter, list mobile, detail satu region, target 44px | Data tidak boleh selalu tersembunyi di bawah control stack |
| **P1 · copy/privacy** | “Sanitized (Aman AI Cloud)” memberi jaminan absolut (`:519–532,639–652,1283–1315`) | “Versi tersamarkan — tinjau sebelum dibagikan”; preview + policy | Regex IPv4/email/sebagian secret tidak menjamin seluruh identitas atau secret hilang |
| **P2 · visual** | Tombol biru/hijau, emoji, glow dan functional text 10–11px | Neutral chrome, semantic severity colors, body 14px/meta 12px, one icon vocabulary | Prioritas berasal dari data, bukan dekorasi yang berteriak bersamaan |

Tidak ada P0 yang dibuktikan pada audit ini. P1 export/privacy adalah risiko source yang perlu ditangani sebelum rollout; bukan klaim exploit atau kebocoran yang telah terjadi.

## Technical findings — Web Interface Guidelines

Reviewer B menghasilkan **12 temuan: 5 P1, 6 P2, 1 P3**. Prioritas cross-workstream pada tabel sebelumnya dikelompokkan ulang, sehingga tidak dijumlahkan dengan hitungan ini.

| Severity | file:line | Temuan dan koreksi |
| --- | --- | --- |
| P1 | `app/index.html:331–340,401–403` | 9 clickable span + 3 sortable th tidak keyboard-reachable; button/link semantics + keyboard sort |
| P1 | `app/index.html:449–453,486–493,573–577,1104–1106,1331–1333` | Modal tidak memiliki dialog semantics/focus trap/Escape/restore; Tab mencapai background |
| P1 | `app/index.html:349–363,400,463–476,552,580–607` | 14 static form controls tidak punya associated label/aria-label; search hanya placeholder fallback |
| P1 | `app/index.html:164,166` | White small text di blue/success fills gagal AA; ganti pair token yang tervalidasi |
| P1 | `app/index.html:46–66,81–85,178,231` | Narrow layout overflow; responsive shell dan container sizing perlu diperbaiki |
| P2 | `app/index.html:296–377,395` | Stacked controls menyingkirkan results; progressive disclosure dan route separation |
| P2 | `app/index.html:105,130,139,160,519–532,935–936` | View buttons 22px, chips 26.5px, checkbox 13px; functional text 10/10.5px. Sub-44px bukan otomatis WCAG AA fail, tetapi buruk untuk touch/precision |
| P2 | `app/index.html:317–319,365,380,620,742–750,778–786` | Tidak ada live region / selected state / aria-sort; expose state dan announce async changes |
| P2 | `app/index.html:374–375,723–789,1416–1474` | URL tidak menyimpan view/filter; export scope tidak konsisten |
| P2 | `app/index.html:1283–1296,1314–1321` | Rejected clipboard Promise masih memunculkan sukses; await/catch dan fallback scoped |
| P2 | `app/index.html:287,667–678` | Health failure tidak mengubah badge hijau; tampilkan offline/stale dan last good update |
| P3 | `app/index.html:106,142,161` | transition: all 150ms tetap aktif saat reduced motion; list property eksplisit dan motion policy |

Focus input sudah mengganti outline dengan cyan border; tidak diklaim seluruh focus indicator hilang. Table punya local overflow container; yang gagal adalah page/header/workflow overflow di luar region itu.

## Detector Impeccable — hasil nyata, bukan daftar bug unik

Command satu kali:

```sh
IMPECCABLE_HOME=/home/nothrovo/.hermes/profiles/luna-hernandez/cache/impeccable \
  sh /home/nothrovo/.hermes/profiles/luna-hernandez/skills/creative/impeccable/scripts/impeccable \
  detect --json app/index.html
```

Exit 2 berarti findings, bukan launcher crash. **25 occurrences: 24 warning + 1 advisory; 22 quality + 3 slop.**

| Rule | Occurrences | Interpretasi |
| --- | ---: | --- |
| low-contrast | 13 | 8 blue, 4 green, 1 gradient advisory; repeated controls, bukan 13 color bugs unik |
| dark-glow | 2 | Duplicate occurrences pada satu source halo logo (`:62`) |
| tiny-text | 3 | Caption 11/11.5px; exact node mapping detector terbatas |
| cramped-padding | 1 | Kemungkinan false positive pada table-card; th/td punya 9px 12px padding |
| undersized-ui-text | 5 | Empat copy controls 10.5px dan hit badge 10.5px |
| overused-font | 1 | Inter sebagai stylistic tell; bukan accessibility atau correctness failure |
| **Total** | **25** | Jangan menyebut ini 25 bug unik |

Semua occurrence output detector melaporkan **line 0**; source mapping dilakukan manual, bukan lokasi presisi dari detector. Tidak ada klaim user-visible overlay atau keseluruhan automated accessibility pass.

## Hallmark audit — subset yang sesuai operational app

| Severity | Named tell | Source | Fix |
| --- | --- | --- | --- |
| Major | Shadow-glow on dark | `index.html:59–62` | Hapus gradient/glow logo; hierarchy melalui tone/type |
| Major | Generic emoji as feature icon | `:287–290,317–340,345–376` | Satu neutral icon vocabulary atau teks tanpa icon |
| Major | Mid-render token improvisation | `:164–169,497–567,927–929` | Semantic tokens untuk semua role dan state |
| Major | transition-all | `:106,142,161` | Property eksplisit; focus instan; motion bermakna saja |
| Minor | Three periods instead of ellipsis | `:349,380,413,464` | Ellipsis typographic pada UI copy |

**Summary: 0 critical · 4 major · 1 minor** pada named Hallmark subset ini. Ini bukan 58-gate certification. Single-family app text dan neutral dark bukan otomatis salah; audit tidak memaksakan font pairing marketing, tinted background atau hero pada SOC console. Macrostructure “Workbench” di katalog Hallmark adalah product tour marketing, sehingga tidak dipaksakan menjadi komposisi app. App-specific guidance dari design-taste/Impeccable lebih sesuai.

## Persona dan emotional journey

- **Power analyst:** shift-click dan dedup membantu; rerender yang menghapus selection dan modal berulang memutus ritme. Solusi: state terpisah + inspector tetap.
- **Keyboard analyst:** filter/sort tidak punya affordance setara dan modal mengirim Tab ke background. Solusi: semantic controls + focus model, bukan shortcut sebagai tambalan.
- **First-time analyst:** strip langkah memberi orientasi, tetapi semua format dan jargon muncul sekaligus. Solusi: first-run empty state dengan Impor sebagai satu next action; bantuan contextual.
- **Emotional journey:** awal tampak meyakinkan karena status hijau dan “aman cloud”, lalu beban pilihan naik. End state harus benar-benar terverifikasi—bukan toast sukses yang tidak menunggu clipboard.

## Skill provenance dan tool limitations

Terpasang di active profile Luna: Impeccable, Awesome Design MD, Hallmark. Loaded/applied: claude-design (surface-first dan alternatives), design-taste-frontend (app-screen rules), popular-web-designs (IBM reference), emil-design-eng (interaction quality), design-md (spec + exports), frontend-design (subject-specific hierarchy), web-design-guidelines (fresh technical rules), serta ketiga skill baru.

- Impeccable context awal gagal karena executable permission; fallback diumumkan. Detector kemudian berhasil dengan `sh` launcher. PRODUCT.md/root DESIGN.md belum ada; tidak diinventasi sebagai existing truth.
- Awesome Design MD bundle berisi README redirects, bukan full DESIGN.md. IBM reference landing diambil, lalu detail prinsip dari installed popular-web-designs IBM template digunakan sebagai fallback yang diidentifikasi.
- design-taste draw gagal karena `scripts/lib/app-draw.mjs` tidak ada. App-screen reference dipakai langsung; tidak ada seed/dealt direction/inspector pass rekaan.
- Proposal dipilih eksplisit, bukan hasil random draw. Screenshot capture parent responsive sempat timeout; DOM geometry tetap dikumpulkan dan screenshot reviewer mobile diperiksa.
- Design spec lint dengan `@google/design.md@0.4.0`: **0 errors, 2 orphan-token warnings** (border/control). Warnings dipertahankan karena role divider/border tidak direpresentasikan component-property whitelist; tidak ada contrast warning pada proposal component pairs. Ini bukan bukti WCAG compliance seluruh UI yang belum dibangun.

## Handoff

Baca `BLUEPRINT.md` untuk sitemap, wireframe, module tree, API gaps, roadmap dan acceptance checklist. Baca `DESIGN.md` untuk draft visual/interaction system; `tokens.json` dan `tokens.css` adalah export proposal, tidak diload production.

Prioritas implementasi: **scope/state safety → shell/router → triage+inspector → case workspace → impor/laporan → accessibility/offline hardening**. Maintain backend stack FastAPI dan native HTML/CSS/ES modules; tidak menambah React/Tailwind hanya untuk redesign.

Questions skipped: user meminta review dan rencana; cukup konteks untuk rekomendasi. Build menunggu persetujuan arah, keputusan cross-tenant case policy dan export scope contract. Tidak ada claim redesign deployed atau prototype interaktif selesai.
