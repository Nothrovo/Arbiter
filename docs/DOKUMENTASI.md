# Arbiter 

## *Dokumentasi Teknis*

| INTERNAL — SOC Lab   \|   Do not share outside authorised named recipients |
| :---: |

## **DOCUMENT CONTROL**

| Document name | Arbiter Technical Documentation | Classification | Internal |
| :---- | :---- | :---- | :---- |
| **Document ID** | SOC-DOC-ARBITER-001 | **Personal data?** | Yes |
| **Version** | 1.0 | **Owner (Data Owner)** | SOC Lab |
| **Status** | Active |  |  |
| **Created by / date** | Made wira Darma Puta / 2026-11-13 | **Reviewed by / date** |  |
| **Next review date** | Yearly | **Retention** | Until superseded; secure erase |

## **VERSION HISTORY**

| Version | Date | Author | Reviewed by | Summary of change |
| :---- | :---- | :---- | :---- | :---- |
| 1.0 | 2026-11-13 | Made Wira Darma Putra | \- | Initial version |

# 

# Dokumentasi Arbiter

**Arbiter** : Meja investigasi SOC untuk telemetri Wazuh yang telah dinormalisasi. Dokumen ini menjelaskan ringkasan, deskripsi, workflow, flowchart, keamanan, cara kerja, komponen, dan langkah instalasi berdasarkan implementasi di repositori ini.

---

## 1\. Ringkasan

Arbiter adalah aplikasi web **airgapped** yang membantu analis SOC mengubah ekspor alert **Wazuh SIEM** yang besar dan repetitif menjadi antrean triage yang ringkas, bukti investigasi yang tertaut, kasus insiden, dan laporan siap dibagikan.

Masalah utama yang diselesaikan:

| Masalah | Pendekatan Arbiter |
| :---- | :---- |
| Ribuan baris log berulang membanjiri analis | Deduplikasi berbasis signature SHA-256, satu baris per serangan berulang |
| Active Response (rule 651/652) terlihat seperti serangan baru | Alert respons diekstrak, ditautkan ke alert asal, tidak dihitung sebagai serangan mandiri |
| IP penyerang berputar-putar | Grouping memakai host \+ rule; IP hanya menjadi facet |
| Verdict otomatis tidak dapat dipertanggungjawabkan | Klasifikasi deterministik dengan `signals` \+ `reason`; rule tak dikenal tetap `needs_review` |
| Data sensitif tidak boleh keluar | Tidak ada cloud, CDN, analytics, atau telemetri; AI lokal opsional via loopback |
| Laporan manual memakan waktu | Ekspor HTML (Google Docs), DOCX, XLSX, TSV, Markdown, CSV dengan scope yang sama |

**Ringkasan satu paragraf:** Arbiter menerima JSON Wazuh (Elasticsearch hits, array, JSONL, atau tempel langsung), membaca struktur bersarang termasuk origin Active Response, menormalisasi alert, menghitung signature stabil, memberi klasifikasi yang dapat diaudit, mengorelasikan respons dengan asalnya, menyimpan ke PostgreSQL, lalu menyediakan triage, AI triage lokal, manajemen insiden, dan ekspor laporan — seluruhnya di lingkungan lokal.

---

## 2\. Deskripsi Produk

### 2.1 Untuk siapa

- Analis SOC yang bekerja dengan Wazuh dan menerima ekspor JSON berukuran besar.  
- Tim IR yang perlu menyusun kronologi serangan dan laporan insiden.  
- Operator airgapped yang tidak mengizinkan data alert keluar dari jaringan.

### 2.2 Batas produk

- **Bukan pengganti Wazuh.** Arbiter membaca, menjelaskan, dan mengorganisasi alert Wazuh; deteksi tetap milik Wazuh.  
- **Tenant adalah konteks kerja, bukan otorisasi.** Pemisahan tenant menjaga scope query/ekspor, tetapi bukan mekanisme izin pengguna.  
- **Tidak ada dashboard dekoratif.** Triage adalah halaman awal.  
- **Tidak ada klaim "aman".** Status kosong selalu dinamai eksplisit: "Belum ada cache", "Tidak ada deteksi", "Perlu ditinjau".  
- **Redaksi bukan jaminan.** Ekspor tersamarkan tetap harus ditinjau sebelum dibagikan.

### 2.3 Destinasi aplikasi

| Rute | Nama | Fungsi |
| :---- | :---- | :---- |
| `#/triage` | Triage | Antrean alert, filter preset, inspector sidebar, korelasi, seleksi massal |
| `#/ai-triage` | AI Triage | Klasifikasi TP/FP dengan Ollama lokal atau rule deterministik, window harian 17:00 WIB |
| `#/realtime` | Realtime | Hitung dan tarik alert langsung dari Wazuh Indexer |
| `#/stats` | Statistik | Pivot multi-dimensi, spotter benign/malicious, drill-down |
| `#/incidents/:id` | Insiden | Editor kasus: bukti, analisis, kesimpulan, rekomendasi |
| `#/imports` | Impor | Unggah file atau tempel JSON Wazuh |
| `#/reports` | Laporan | Ekspor sesuai scope (HTML, DOCX, XLSX, TSV, Markdown, CSV) |
| `#/database` | Database | Profil PostgreSQL lokal/remote dan pemeliharaan dengan pratinjau |
| `#/settings` | Pengaturan | Koneksi Wazuh Indexer, Ollama, realtime, preferensi sidebar |
| `#/wazuh-queries` | Wazuh Queries | Catatan dan pustaka query Wazuh |
| `#/error-codes` | Error Codes | Referensi kode error |

### 2.4 Kemampuan inti

1. **Ingesti multi-format** — Elasticsearch `hits.hits[]`, array JSON, JSON Lines, objek tunggal, unggah file, dan tempel langsung.  
2. **Pembacaan Wazuh bersarang** — origin alert dari `data.parameters.alert` atau JSON di `full_log`; metadata Vulnerability Detector dari `data.vulnerability`.  
3. **Deduplikasi** — signature stabil atas `(tenant, agent, rule_id, srcip, normalized_log)`; `hit_count` dan rentang `first_seen → last_seen`.  
4. **Klasifikasi auditable** — `tp` / `fp` / `needs_review`, `role` (`indicator` / `response` / `context` / `unknown`), `priority`, `confidence`, `signals`, `reason`.  
5. **Korelasi** — respons aktif menempel ke alert asal; grup kanonik `(agent_name, rule_id)`; rantai serangan berurutan lintas rule.  
6. **AI Triage lokal** — Ollama loopback opsional, fallback deterministik, penguncian true-positive untuk indikator exploit (`lock_tp`).  
7. **Multi-tenant** — ekstraksi `agent.labels.tenant`, pemilih tenant, dan penjagaan agar satu grup tidak mencampur dua tenant.  
8. **Manajemen insiden** — bukti, analisis, kesimpulan, rekomendasi, status, severity, verdict.  
9. **Threat intelligence lokal** — join `source_ip` ke `public.ip_intel_cache`; AbuseIPDB hanya dipanggil eksplisit oleh pengguna.  
10. **Ekspor resmi** — 6 jalur keluaran dengan scope konsisten dan batas 10.000 alert per ekspor (413 jika melebihi; tidak pernah file parsial).  
11. **Autentikasi lokal** — pengguna admin/analyst, sesi terenkripsi, password PBKDF2, kredensial terenkripsi di database.

---

## 3\. Workflow

### 3.1 Workflow analis (harian)

1. **Masuk** ke Arbiter dan pilih tenant aktif (atau `Semua tenant`).  
2. **Impor** ekspor Wazuh di `#/imports`, atau tarik alert langsung dari `#/realtime`.  
3. **Tinjau hasil AI Triage** di `#/ai-triage`: pilih tenant, severity band, limit alert, dan basis grouping (`Deskripsi Rule` atau `Host / Agent + Rule`).  
4. **Buka grup** dengan `Buka di Triage`; inspector menampilkan log, origin bersarang, sinyal klasifikasi, dan intel IP.  
5. **Korelasi** untuk melihat grup host+rule, respons tertaut, facet IP, dan rantai tahapan.  
6. **Pilih bukti** (Shift+Click untuk rentang), lalu **Buat insiden** atau **Simpan ke Insiden** dari AI Triage.  
7. **Tulis** analisis, kesimpulan, dan rekomendasi di editor insiden.  
8. **Ekspor** di `#/reports` sesuai scope: filter aktif, kasus insiden, atau alert terpilih.  
9. **Tandai review** (Pending/Reviewed) setelah tindak lanjut.

### 3.2 Workflow data

```
Impor / Realtime
      │
      ▼
Parser (multi-format, salvage control byte)
      │
      ▼
Normalisasi (tenant, agent, rule, IP, MITRE, CVE, signature)
      │
      ▼
Deduplikasi (SHA-256 stabil; hit_count, first_seen, last_seen)
      │
      ▼
Klasifikasi (verdict, role, priority, confidence, signals, reason)
      │
      ▼
Korelasi (respons → origin, grup kanonik, rantai serangan)
      │
      ▼
PostgreSQL (wazuh.alerts, parsed_details JSONB)
      │
      ├── Triage & filter
      ├── AI Triage (grup + window 17:00 WIB)
      ├── Insiden (analysis_groups + alert_group_members)
      └── Laporan (ekspor ter-scope)
```

### 3.3 Siklus hidup insiden

```
Alert masuk → Triage → Pilih bukti → Buat/Simpan insiden
      → Analisis → Kesimpulan → Rekomendasi
      → Status (open/closed) → Ekspor → Arsip
```

Kebijakan penting: kasus dengan scope tenant **wajib** memiliki bukti di tenant tersebut. Kasus tanpa bukti hanya boleh dibuat dari scope `Semua tenant`. Penghapusan bukti terakhir dalam scope tenant ditolak sebelum mutasi.

---

## 4\. Flowchart

### 4.1 Alur end-to-end

```
flowchart TD
    A["Wazuh Indexer / ekspor JSON<br/>ES hits, array, JSONL, paste"] --> B["Impor #/imports<br/>atau Realtime #/realtime"]
    B --> C["Parser<br/>access, syslog, sshd, PAM,<br/>audit, AppArmor, JSON, control-byte salvage"]
    C --> D["Normalisasi<br/>tenant, agent, rule, source_ip,<br/>MITRE, CVE, parsed_details"]
    D --> E["Deduplikasi<br/>SHA-256 signature stabil"]
    E --> F["Klasifikasi deterministik<br/>tp / fp / needs_review<br/>role, priority, confidence, signals"]
    F --> G["Korelasi<br/>response → origin, host+rule,<br/>facet IP, rantai serangan"]
    G --> H[("PostgreSQL<br/>wazuh.alerts<br/>parsed_details JSONB")]
    H --> I["Triage<br/>filter, inspector, seleksi"]
    H --> J["AI Triage<br/>Ollama lokal / rule fallback<br/>window 17:00 WIB"]
    I --> K["Insiden<br/>bukti, analisis,<br/>kesimpulan, rekomendasi"]
    J -->|"Buka di Triage"| I
    J -->|"Simpan ke Insiden"| K
    K --> L["Laporan #/reports<br/>HTML, DOCX, XLSX,<br/>TSV, Markdown, CSV"]
    I --> L

    M["Autentikasi lokal<br/>admin / analyst"] -.->|"gate semua /api/*"| B
    M -.-> I
    M -.-> K
    M -.-> L

    N["Wazuh Indexer<br/>settings tersimpan terenkripsi"] -.-> B
    O["Ollama loopback<br/>opsional"] -.-> J
    P[("ip_intel_cache<br/>reputasi lokal")] -.-> I
```

### 4.2 Pemisahan peran event

```
flowchart LR
    R["Alert Wazuh"] --> Q{"Ada origin<br/>bersarang?"}
    Q -->|"Ya, rule 651/652"| S["role = response<br/>verdict = fp (mandiri)<br/>origin_verdict = tp"]
    Q -->|"Tidak"| T{"Profil rule dikenal?"}
    T -->|"Indikator serangan"| U["role = indicator<br/>verdict = tp"]
    T -->|"Admin / maintenance /<br/>siklus CVE"| V["role = context<br/>verdict = fp"]
    T -->|"Tidak dikenal"| W["role = unknown<br/>verdict = needs_review"]
    S --> X["Tempel ke grup origin<br/>di correlate_alerts()"]
    U --> Y["Grup kanonik + chain"]
    V --> Y
    W --> Y
```

### 4.3 Batas kepercayaan (trust boundary)

```
flowchart TB
    subgraph Local["Lingkungan lokal / airgapped"]
        UI["Browser analis"]
        APP["FastAPI Arbiter<br/>:8000"]
        PG[("PostgreSQL")]
        IDX["Wazuh Indexer"]
        OLL["Ollama loopback/LAN"]
        INTEL[("IP Intel lokal")]
        UI -->|"cookie sesi HttpOnly"| APP
        APP --> PG
        APP -->|"HTTPS / TLS opsional"| IDX
        APP -->|"http lokal"| OLL
        APP --> INTEL
    end
    APP -.->|"HANYA aksi eksplisit<br/>AbuseIPDB enrichment"| EXT["api.abuseipdb.com"]
```

---

## 5\. Cara Kerja

### 5.1 Ingesti dan parsing

- `app/parser.py` mendukung Elasticsearch `hits.hits[]`, array JSON, JSONL, dan objek tunggal.  
- Parser memakai `strict=False` untuk menyelamatkan log dengan karakter kontrol tanpa membuang event valid.  
- Regex khusus mengekstrak web access log (Apache/Nginx), `sshd`, PAM, sudo, audit kernel, AppArmor, serta URL/metode/status di dalam syslog generik.  
- Re-ingest alert Wazuh yang identik dikenali dan diabaikan (safeguard duplikasi berdasarkan identitas alert).

### 5.2 Normalisasi

`app/core.py` menghasilkan satu baris normalisasi dengan:

| Kelompok | Field |
| :---- | :---- |
| Identitas | `alert_id`, `wazuh_id`, `tenant`, `timestamp` |
| Target | `agent_name`, `agent_ip`, `location` |
| Rule | `rule_id`, `rule_level`, `description`, `rule_groups`, `decoder` |
| Jaringan/aktor | `source_ip`, `parsed_details`, `data` |
| Konteks | `mitre_ids`, `cve` |
| Bukti | `full_log`, `raw`, `previous_output` |
| Grouping | `log_signature`, `hit_count`, `first_seen`, `last_seen` |
| Workflow | `is_reviewed`, `reviewer_notes` |
| Intelijen | `parsed_details.wazuh_intel` |

`parsed_details` adalah JSONB aditif, sehingga baseline tidak memerlukan migrasi skema.

### 5.3 Deduplikasi

Signature SHA-256 dihitung dari `(tenant, agent, rule_id, srcip, normalized_log)`. Alert berulang digabung menjadi satu baris dengan jumlah hit dan rentang waktu. Ini mengubah puluhan ribu baris scan menjadi beberapa baris triage.

### 5.4 Klasifikasi

`app/wazuh_intel.py` memakai profil rule kuratif, lalu fallback ke grup/keyword. Prinsip:

- `verdict` hanya `tp`, `fp`, atau `needs_review`.  
- `role` memisahkan `indicator`, `response`, `context`, dan `unknown`.  
- `priority` adalah urgensi, bukan verdict.  
- `confidence` adalah kekuatan bukti, bukan probabilitas.  
- `signals` adalah daftar "mengapa verdict ini"; tanpa sinyal, tidak ada klaim.  
- Rule tak dikenal tetap `needs_review` meskipun `rule.level` tinggi.  
- IP known-bad dan severity tinggi menaikkan **priority**, tidak menciptakan verdict TP.

Contoh hasil klasifikasi:

```json
{
  "verdict": "fp",
  "role": "response",
  "family": "active_response",
  "priority": "low",
  "confidence": 0.99,
  "reason": "Active Response 'add' adalah tindakan containment turunan…",
  "signals": [
    {"code": "rule_profile", "label": "Profil rule", "value": "Rule 651", "kind": "rule"},
    {"code": "origin_link", "label": "Alert asal", "value": "origin-alert-5710", "kind": "correlation"}
  ],
  "origin": {"alert_id": "…", "rule_id": "5710", "source_ip": "…"},
  "origin_verdict": "tp"
}
```

### 5.5 Korelasi

- Respons aktif (651/652) ditautkan ke alert asal melalui `data.parameters.alert` atau JSON di `full_log`.  
- Identitas grup kanonik berurutan:  
  1. `(agent_name, rule_id)`  
  2. `log_signature`  
  3. `(source_ip, rule_id)`  
  4. alert itu sendiri  
- Source IP adalah **facet**, bukan kunci grup; IP yang berputar tetap satu grup.  
- `build_attack_chains()` mengelompokkan `(agent_name, source_ip)` lintas rule untuk menjelaskan urutan seperti: `5710 invalid SSH user → 5715 login sukses → 5402 sudo root → 2833 crontab berubah`.  
- Rantai adalah bukti penjelas, bukan verdict.

### 5.6 AI Triage lokal

- Engine ganda: Ollama lokal (`http://127.0.0.1:11434`) bila diaktifkan, atau rule deterministik (`local_rules` / `local_rules_fallback`).  
- Filter: tenant, severity band (`Low 0–6`, `Medium 7–11`, `High 12–14`, `Critical 15+`), limit alert 1–5000.  
- Grouping: `rule_description` atau `host_rule`, dengan penjagaan satu tenant per grup.  
- Hasil disimpan di `wazuh.app_settings` dan dipulihkan saat halaman dibuka.  
- Window harian: alert baru digabung ke grup yang ada bila terjadi sebelum **17:00 WIB (UTC+7)**; setelah itu masuk window hari berikutnya.  
- `lock_tp`: indikator exploit terverifikasi (path traversal/LFI, scanner, payload RCE/SQLi/JNDI) mengunci verdict `tp`, meskipun status HTTP 400/403/404 atau model lokal mencoba menurunkannya.  
- Payload ke model tidak memuat raw log atau alert ID; `safe_alerts()` menghapus `raw`, `data`, `full_log`, `parsed_details`, dan `duplicate_instances`.

### 5.7 Triage dan insiden

- Filter preset: 403, 404 Probes, Repeating, Bot, Curl, Non-HTTP.  
- Seleksi berbasis `Set` yang bertahan saat re-render dan perubahan filter; Shift+Click untuk rentang.  
- Inspector memakai detail version guard: respons API yang sudah usang dibuang.  
- Insiden menyimpan `analysis_groups` \+ `alert_group_members`.  
- Kebijakan empty case dan tenant-scoped evidence dijelaskan di bagian 3.3.

### 5.8 Threat intelligence dan redaksi

- `source_ip` di-join ke `public.ip_intel_cache` (AbuseIPDB score, VirusTotal malicious, ISP, negara).  
- Cache kosong ditampilkan sebagai "Belum ada cache"; tidak ada deteksi sebagai "Tidak ada deteksi".  
- `app/privacy.py` meredaksi IP privat/publik/loopback, password/token, dan email secara deterministik.  
- Disclaimer wajib: **"Versi tersamarkan—tinjau sebelum dibagikan"**.

### 5.9 Ekspor

Scope ekspor menormalkan filter yang sama untuk semua format, membuang pagination, dan membatasi **10.000 alert**. Jika melebihi, API mengembalikan **413** secara eksplisit; tidak ada file parsial.

| Format | Endpoint | Kegunaan |
| :---- | :---- | :---- |
| HTML | `/api/export/report-html` | Tempel ke Google Docs |
| DOCX | `/api/export/docx` | Laporan formal landscape |
| XLSX | `/api/export/xlsx` | Spreadsheet multi-kolom \+ intel |
| TSV | `/api/export/tsv` | Tempel ke spreadsheet |
| Markdown | `/api/export/markdown` | Ringkasan insiden |
| CSV | `/api/export/csv` | Data mentah ter-scope |

---

## 6\. Komponen yang Dipakai

```
.
├── .ai/
│   ├── agents/
│   │   ├── code-reviewer.md
│   │   └── security-auditor.md
│   ├── commands/
│   │   ├── fix-issue.md
│   │   └── review.md
│   ├── hooks/
│   │   └── validate-bash.sh
│   ├── rules/
│   │   ├── api-conventions.md
│   │   ├── code-style.md
│   │   └── testing.md
│   ├── skills/
│   │   └── deploy/
│   │       ├── SKILL.md
│   │       └── deploy-config.md
│   ├── settings.json
│   └── settings.local.json
├── app/
│   ├── static/
│   │   ├── fonts/
│   │   │   ├── IBMPlexMono-Regular.woff2
│   │   │   ├── IBMPlexSans-Medium.woff2
│   │   │   ├── IBMPlexSans-Regular.woff2
│   │   │   ├── IBMPlexSans-SemiBold.woff2
│   │   │   └── OFL.txt
│   │   ├── img/
│   │   │   └── favicon.svg
│   │   ├── js/
│   │   │   ├── api/
│   │   │   │   └── client.js
│   │   │   ├── features/
│   │   │   │   ├── ai-triage/
│   │   │   │   │   ├── model.js
│   │   │   │   │   └── view.js
│   │   │   │   ├── database/
│   │   │   │   │   ├── model.js
│   │   │   │   │   └── view.js
│   │   │   │   ├── error-codes/
│   │   │   │   │   ├── model.js
│   │   │   │   │   └── view.js
│   │   │   │   ├── imports/
│   │   │   │   │   ├── model.js
│   │   │   │   │   ├── render.js
│   │   │   │   │   └── view.js
│   │   │   │   ├── incidents/
│   │   │   │   │   ├── model.js
│   │   │   │   │   ├── render.js
│   │   │   │   │   ├── state.js
│   │   │   │   │   ├── view.js
│   │   │   │   │   └── workspace.js
│   │   │   │   ├── realtime/
│   │   │   │   │   └── view.js
│   │   │   │   ├── reports/
│   │   │   │   │   ├── model.js
│   │   │   │   │   ├── render.js
│   │   │   │   │   └── view.js
│   │   │   │   ├── settings/
│   │   │   │   │   ├── model.js
│   │   │   │   │   └── view.js
│   │   │   │   ├── stats/
│   │   │   │   │   ├── model.js
│   │   │   │   │   ├── render.js
│   │   │   │   │   └── view.js
│   │   │   │   ├── triage/
│   │   │   │   │   ├── model.js
│   │   │   │   │   └── view.js
│   │   │   │   └── wazuh-queries/
│   │   │   │       ├── model.js
│   │   │   │       └── view.js
│   │   │   ├── state/
│   │   │   │   ├── navigation.js
│   │   │   │   ├── scope.js
│   │   │   │   ├── selection.js
│   │   │   │   ├── sidebar.js
│   │   │   │   ├── stats.js
│   │   │   │   ├── triage.js
│   │   │   │   └── workspace.js
│   │   │   ├── ui/
│   │   │   │   ├── charts.js
│   │   │   │   ├── primitives.js
│   │   │   │   └── theme.js
│   │   │   ├── app.js
│   │   │   ├── feature-loader.js
│   │   │   └── router.js
│   │   └── styles/
│   │       ├── base.css
│   │       ├── components.css
│   │       ├── ledger.css
│   │       ├── shell.css
│   │       ├── themes.css
│   │       └── tokens.css
│   ├── __init__.py
│   ├── ai_triage.py
│   ├── auth.py
│   ├── config.py
│   ├── core.py
│   ├── database.py
│   ├── exports.py
│   ├── index.html
│   ├── intel.py
│   ├── main.py
│   ├── parser.py
│   ├── privacy.py
│   ├── query.py
│   ├── secure_store.py
│   ├── settings.py
│   └── wazuh_intel.py
├── docker/
│   ├── nginx/
│   │   └── default.conf
│   └── postgres/
│       └── init.sql
├── docs/
│   ├── superpowers/
│   │   └── plans/
│   │       ├── 2026-10-23-arbiter-enrichment-reports-favicon-correlation.md
│   │       └── 2026-10-27-alert-statistics-pivot.md
│   ├── ui-ux-redesign/
│   │   ├── evidence/
│   │   │   ├── baseline-1280.json
│   │   │   ├── baseline-responsive.json
│   │   │   ├── before-1280.png
│   │   │   ├── before-mobile.png
│   │   │   ├── detector-findings.json
│   │   │   ├── reviewer-b-fixed-layouts.json
│   │   │   ├── reviewer-b-report.json
│   │   │   └── verification.json
│   │   ├── implementation-evidence/
│   │   │   ├── incident-desktop.png
│   │   │   ├── responsive-triage.json
│   │   │   ├── route-geometry.json
│   │   │   ├── triage-desktop.png
│   │   │   └── triage-mobile.png
│   │   ├── AUDIT.md
│   │   ├── BLUEPRINT.md
│   │   ├── DESIGN.md
│   │   ├── IMPLEMENTATION-CONTRACT.md
│   │   ├── README.md
│   │   ├── tokens.css
│   │   └── tokens.json
│   ├── ARCHITECTURE.md
│   ├── ARSITEKTUR.md
│   ├── AUTONOMOUS_ENGINEERING_SOP.md
│   └── DOKUMENTASI.md
├── scripts/
│   ├── diagnose_realtime_pull.py
│   └── setup-ai-symlinks.sh
├── tests/
│   ├── frontend/
│   │   ├── ai-triage.test.mjs
│   │   ├── charts.test.mjs
│   │   ├── client.test.mjs
│   │   ├── database-gates.test.mjs
│   │   ├── database-trust.test.mjs
│   │   ├── database-workspace.test.mjs
│   │   ├── database.test.mjs
│   │   ├── evidence-ledger.test.mjs
│   │   ├── feature-loader.test.mjs
│   │   ├── imports-view.test.mjs
│   │   ├── imports.test.mjs
│   │   ├── incidents-model.test.mjs
│   │   ├── incidents-policy.test.mjs
│   │   ├── incidents-render.test.mjs
│   │   ├── incidents-state.test.mjs
│   │   ├── incidents-view.test.mjs
│   │   ├── intel-cache.test.mjs
│   │   ├── navigation-state.test.mjs
│   │   ├── primitives.test.mjs
│   │   ├── realtime.test.mjs
│   │   ├── reports-view.test.mjs
│   │   ├── reports.test.mjs
│   │   ├── router-history.test.mjs
│   │   ├── router.test.mjs
│   │   ├── scope-edge.test.mjs
│   │   ├── scope.test.mjs
│   │   ├── selection.test.mjs
│   │   ├── settings.test.mjs
│   │   ├── shell.test.mjs
│   │   ├── sidebar.test.mjs
│   │   ├── stats-refinement.test.mjs
│   │   ├── stats-trust.test.mjs
│   │   ├── stats.test.mjs
│   │   ├── triage-refresh.test.mjs
│   │   ├── triage-request.test.mjs
│   │   ├── triage-summary.test.mjs
│   │   ├── triage.test.mjs
│   │   └── workspace.test.mjs
│   ├── __init__.py
│   ├── test_ai_triage.py
│   ├── test_api.py
│   ├── test_database_trust.py
│   ├── test_dedup.py
│   ├── test_exports.py
│   ├── test_intel_cache.py
│   ├── test_parser.py
│   ├── test_privacy.py
│   ├── test_settings.py
│   ├── test_stats.py
│   ├── test_triage_scope.py
│   ├── test_ui_api.py
│   ├── test_ui_safety.py
│   └── test_wazuh_intel.py
├── .dockerignore
├── .env.example
├── .gitattributes
├── .gitignore
├── .mcp.json
├── AGENTS.local.md
├── AGENTS.md
├── Dockerfile
├── PRODUCT.md
├── README.md
├── compose.override.yaml
├── compose.yaml
├── package-lock.json
├── package.json
├── requirements.txt
└── start.sh
```

### 6.1 Stack

| Lapisan | Teknologi | Catatan |
| :---- | :---- | :---- |
| Backend | Python 3.11+, FastAPI, Uvicorn | Entry `app/main.py`, versi API 2.0.0 |
| Database | PostgreSQL 16+ via `psycopg` 3 | Skema `wazuh`, tabel intel `public` |
| Frontend | JavaScript ES modules \+ CSS native | Tanpa React/Vue/Angular/Tailwind |
| Tipografi | IBM Plex Sans/Mono lokal (OFL) | `app/static/fonts/` |
| Desain | Token CSS di `app/static/styles/tokens.css` | Arah **Quiet Evidence Desk** |
| Dokumen | `python-docx`, `openpyxl` | DOCX dan XLSX |
| Enkripsi | `cryptography` (Fernet) \+ PBKDF2-HMAC-SHA256 | Kredensial dan hash password |
| AI lokal | Ollama (opsional) | Loopback/LAN saja |
| Kontainer | Docker \+ Docker Compose | `network_mode: host` |
| Pengujian | `unittest`, `node --test` | Fixture sintetis |

### 6.2 Modul backend

| Berkas | Tanggung jawab |
| :---- | :---- |
| `app/main.py` | Aplikasi FastAPI, middleware auth, seluruh endpoint REST |
| `app/core.py` | Normalisasi, deduplikasi, signature, grouping dasar |
| `app/parser.py` | Dissector log multi-format dan salvage karakter kontrol |
| `app/wazuh_intel.py` | Baca alert bersarang, indikator payload, klasifikasi, korelasi, chain |
| `app/ai_triage.py` | Clustering AI, Ollama, fallback rule, window 17:00 WIB, `lock_tp` |
| `app/settings.py` | Penyimpanan pengaturan Wazuh, realtime, AI, intel, UI |
| `app/secure_store.py` | Enkripsi Fernet dan pengelolaan kunci lokal |
| `app/auth.py` | Pengguna, PBKDF2, sesi terenkripsi, role admin/analyst |
| `app/database.py` | Koneksi, skema, profil lokal/remote, token pratinjau purge |
| `app/query.py` | Query builder, filter preset, spotter malicious |
| `app/intel.py` | Cache reputasi IP, AbuseIPDB opsional, sinkronisasi remote |
| `app/privacy.py` | Redaktor deterministik |
| `app/exports.py` | Generator HTML, DOCX, XLSX, TSV, Markdown, CSV |

### 6.3 Modul frontend

| Berkas | Tanggung jawab |
| :---- | :---- |
| `app/static/js/app.js` | Kontroler shell, inisialisasi router, health probe |
| `app/static/js/router.js` | Hash router dan guard navigasi |
| `app/static/js/api/client.js` | Fetch same-origin, timeout, ekstraksi error |
| `app/static/js/state/` | Scope, selection, triage, navigation, sidebar, workspace |
| `app/static/js/ui/primitives.js` | `esc()`, ikon, severity, format waktu, empty state |
| `app/static/js/features/` | `triage`, `ai-triage`, `realtime`, `stats`, `incidents`, `imports`, `reports`, `database`, `settings`, `wazuh-queries`, `error-codes` |

### 6.4 Skema database

| Tabel | Isi |
| :---- | :---- |
| `wazuh.alerts` | Alert ternormalisasi, `raw` JSONB, `parsed_details` JSONB (termasuk `wazuh_intel`), status review |
| `wazuh.analysis_groups` | Kasus insiden: judul, kategori, analisis, kesimpulan, rekomendasi, status, severity, source, verdict |
| `wazuh.alert_group_members` | Relasi bukti alert ↔ insiden |
| `wazuh.app_settings` | Pengaturan, pengguna auth, profil database, state AI Triage, formula query |
| `public.ip_intel_cache` | Cache reputasi IP (AbuseIPDB, VirusTotal, ISP, negara) |
| `public.ip_intel_reputation` | Tabel milik provider IP Intel (Remote), dibaca read-only — tidak dibuat Arbiter |

Sumber kebenaran skema ada di `SCHEMA_SQL` (`app/database.py`), bukan hanya
`docker/postgres/init.sql`. Saat startup, `init_database()` menjalankan seluruh
`SCHEMA_SQL` lalu migrasi idempoten:

```sql
ALTER TABLE wazuh.analysis_groups
  ADD COLUMN IF NOT EXISTS verdict TEXT NOT NULL DEFAULT 'needs_review';
```

Dengan demikian database lokal selalu menyusul skema terbaru, sedangkan
`init.sql` hanya dipakai untuk inisialisasi awal container PostgreSQL.

#### 6.4.1 `wazuh.alerts`

| Kolom | Tipe | Keterangan |
| :---- | :---- | :---- |
| `id` | `BIGSERIAL PK` | Primary key internal, dipakai `alert_group_members.alert_pk` |
| `alert_id` | `TEXT NOT NULL DEFAULT ''` | ID alert dari Wazuh |
| `timestamp` | `TEXT` | Waktu event (string ISO-8601, bukan `timestamptz`) |
| `tenant` | `TEXT NOT NULL DEFAULT 'Default'` | Konteks workspace |
| `agent_name`, `agent_ip` | `TEXT` | Agen pelapor |
| `rule_id` | `TEXT` | ID rule Wazuh |
| `rule_level` | `INTEGER` | Level severity Wazuh |
| `description` | `TEXT NOT NULL DEFAULT ''` | Deskripsi rule |
| `rule_groups` | `JSONB DEFAULT '[]'` | Grup rule |
| `decoder` | `TEXT` | Decoder Wazuh |
| `location` | `TEXT` | Lokasi log |
| `source_ip` | `TEXT` | Join key ke `public.ip_intel_cache.ip` |
| `mitre_ids` | `JSONB DEFAULT '[]'` | MITRE ATT&CK |
| `cve` | `TEXT` | CVE terkait |
| `data` | `JSONB DEFAULT '{}'` | Field terstruktur pasca-parsing |
| `raw` | `JSONB NOT NULL` | Payload asli |
| `log_signature` | `TEXT DEFAULT ''` | Sidik jari dedup |
| `hit_count` | `INTEGER DEFAULT 1` | Jumlah duplikat terlipat |
| `first_seen`, `last_seen` | `TEXT` | Rentang kemunculan duplikat |
| `wazuh_ids` | `JSONB DEFAULT '[]'` | Kumpulan ID Wazuh yang terlipat |
| `duplicate_instances` | `JSONB DEFAULT '[]'` | Instance duplikat |
| `parsed_details` | `JSONB DEFAULT '{}'` | Detail parsing + `wazuh_intel` |
| `is_reviewed` | `BOOLEAN NOT NULL DEFAULT false` | Status review |
| `reviewed_at` | `TIMESTAMPTZ` | Waktu review |
| `reviewer_notes` | `TEXT DEFAULT ''` | Catatan reviewer |
| `imported_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | Waktu ingest |

Constraint: `UNIQUE(alert_id, timestamp, agent_name, rule_id)` — target
`ON CONFLICT` pada `ingest_alert_with_dedup()`.

`parsed_details` berisi `status`, `http_status`, `method`,
`path`/`uri`/`url_path`, `ua`/`user_agent`, `referer`, `log_type`
(`http`, `text`, `syslog`, `json`), dan `wazuh_intel`. Objek `wazuh_intel`
hasil `classify_alert()` memuat `verdict` (`tp`/`fp`/`needs_review`), `role`
(`indicator`/`response`/`unknown`), `family`, `priority`, `confidence`,
`reason`, `signals[]`, `source`, `origin`, `origin_verdict`,
`known_bad_source`, serta `response_command`/`response_program` untuk
active-response.

#### 6.4.2 `wazuh.analysis_groups`

| Kolom | Tipe | Default |
| :---- | :---- | :---- |
| `id` | `UUID PRIMARY KEY` | — |
| `title` | `TEXT NOT NULL` | — |
| `category` | `TEXT NOT NULL` | `''` |
| `analysis` | `TEXT NOT NULL` | `''` |
| `conclusion` | `TEXT NOT NULL` | `''` |
| `recommendation` | `TEXT NOT NULL` | `''` |
| `status` | `TEXT NOT NULL` | `'open'` |
| `severity` | `TEXT NOT NULL` | `'medium'` |
| `source` | `TEXT NOT NULL` | `'human'` (`human`/`ai`) |
| `verdict` | `TEXT NOT NULL` | `'needs_review'` |
| `created_at`, `updated_at` | `TIMESTAMPTZ NOT NULL` | `now()` |

Tidak ada `CHECK`/enum di database; validasi status, severity, dan verdict
dilakukan di aplikasi.

#### 6.4.3 `wazuh.alert_group_members`

| Kolom | Tipe | Keterangan |
| :---- | :---- | :---- |
| `alert_pk` | `BIGINT` | `REFERENCES wazuh.alerts(id) ON DELETE CASCADE` |
| `group_id` | `UUID` | `REFERENCES wazuh.analysis_groups(id) ON DELETE CASCADE` |

`PRIMARY KEY (alert_pk, group_id)`. Karena urutan kolom PK diawali
`alert_pk`, pencarian per kasus (`WHERE group_id = %s`) tidak memakai index
dan harus sequential scan.

#### 6.4.4 `wazuh.app_settings`

| Kolom | Tipe | Keterangan |
| :---- | :---- | :---- |
| `key` | `TEXT PRIMARY KEY` | Nama dokumen |
| `value` | `JSONB NOT NULL DEFAULT '{}'` | Isi dokumen |
| `updated_at` | `TIMESTAMPTZ NOT NULL DEFAULT now()` | Waktu tulis terakhir |

Dokumen diakses lewat `load_document()`/`save_document()` dengan upsert
`ON CONFLICT (key)`. Key yang dipakai:

| Key | Isi |
| :---- | :---- |
| `app` | Pengaturan utama: `wazuh` (URL Indexer, username, `password_enc` terenkripsi, pola index, `verify_tls`), `realtime`, `ai`, `intel` (`abuseipdb_key_enc`), `ui` |
| `auth_users` | Daftar pengguna: `username`, `display_name`, `role`, `password_hash` (PBKDF2-HMAC-SHA256 120k iterasi), timestamp |
| `db_profiles` | `remote_url_enc` — URI database Remote terenkripsi Fernet |
| `ai_triage_state` | State AI Triage global |
| `ai_triage_state_<tenant>` | State AI Triage per-tenant |
| `wazuh_query_formulas` | Formula query Wazuh yang disimpan analis |

Tidak ada kolom tenant atau user: pemisahan konteks dilakukan di level dokumen
dan oleh lapisan aplikasi.

#### 6.4.5 `public.ip_intel_cache`

| Kolom | Tipe | Keterangan |
| :---- | :---- | :---- |
| `ip` | `TEXT PRIMARY KEY` | Alamat IP |
| `abuse_score` | `INTEGER` | Skor AbuseIPDB |
| `vt_malicious` | `INTEGER` | Deteksi VirusTotal |
| `country_code` | `TEXT` | Kode negara |
| `isp` | `TEXT` | ISP |
| `attack_types` | `TEXT[] DEFAULT '{}'` | Jenis serangan |
| `total_alert_count` | `INTEGER DEFAULT 1` | Jumlah alert terkait |
| `last_seen` | `TIMESTAMPTZ DEFAULT now()` | Terakhir terlihat |

Tabel ini di-`LEFT JOIN` ke `alerts.source_ip` pada triage, statistik, dan
tampilan detail.

#### 6.4.6 Tabel Remote milik provider

`public.ip_intel_reputation` dibaca read-only lewat profil database `remote`
(`app/intel.py`): `ip`, `abuse_score`, `country_code`, `isp`,
`reputation_json` (JSONB), `reputation_checked_at`. Skema dimiliki sistem
IP Intel (Neuropetra); Arbiter hanya membaca dan mem-join ke
`ip_intel_cache`.

#### 6.4.7 Indeks performa

Seluruh index berada di `wazuh.alerts`:

| Index | Kolom |
| :---- | :---- |
| `idx_wazuh_alerts_source_ip` | `(source_ip)` |
| `idx_wazuh_alerts_rule_id` | `(rule_id)` |
| `idx_wazuh_alerts_timestamp` | `(timestamp)` |
| `idx_wazuh_alerts_tenant` | `(tenant)` |
| `idx_wazuh_alerts_sig` | `(tenant, log_signature)` |
| `idx_wazuh_alerts_reviewed` | `(is_reviewed)` |
| `idx_wazuh_alerts_tenant_timestamp` | `(tenant, timestamp)` |
| `idx_wazuh_alerts_rule_level` | `(rule_level)` |
| `idx_wazuh_alerts_agent_name` | `(agent_name)` |
| `idx_wazuh_alerts_status` | `((parsed_details->>'status'))` |

Tidak ada index GIN untuk `raw`, `data`, `parsed_details`, `mitre_ids`, atau
`rule_groups`. Pencarian teks bebas (`raw::text ILIKE`, `parsed_details::text
ILIKE`) berjalan sebagai scan. Kolom high-cardinality seperti `user_agent`,
`url_path`, `referer` sengaja tidak diberi index btree agar tidak membengkak
pada ingest volume tinggi.

#### 6.4.8 Catatan operasional

- `init.sql` tidak membuat `wazuh.app_settings`; tabel itu dibuat oleh
  `SCHEMA_SQL` saat aplikasi start. Untuk profil `standalone` hal ini aman,
  tetapi `init.sql` bukan cermin skema lengkap.
- `analysis_groups` dan `alert_group_members` belum punya index sekunder;
  listing/purge kasus dan pencarian member per kasus akan scan saat data
  membesar.
- `timestamp`, `first_seen`, dan `last_seen` adalah `TEXT`, sehingga filter
  rentang mengandalkan urutan leksikografis ISO-8601.

### 6.5 Kelompok endpoint API

| Kelompok | Contoh |
| :---- | :---- |
| Kesehatan | `GET /health`, `GET /api/health` |
| Auth | `POST /api/auth/login`, `/logout`, `GET /api/auth/me`, CRUD `/api/auth/users` |
| Ingesti | `POST /api/import`, `POST /api/import-text` |
| Alert | `GET /api/alerts`, `GET /api/alerts/{id}`, review, batch review, full logs |
| Intel | `POST /api/intel/cache/test`, `POST /api/intel/enrich` |
| Insiden | CRUD `/api/groups`, member add/remove |
| Statistik | `GET /api/stats`, `POST /api/stats/facet-alert-ids`, `GET /api/triage/summary` |
| Korelasi | `GET /api/suggestions` |
| Realtime | `GET /api/realtime/count`, `POST /api/realtime/pull` |
| AI | `POST /api/ai/test`, `GET/POST /api/ai/triage`, `POST /api/ai/triage/save` |
| Ekspor | `/api/export/preview`, `/report-html`, `/docx`, `/xlsx`, `/tsv`, `/markdown`, `/csv` |
| Privasi | `POST /api/sanitize-logs` |
| Pengaturan | `GET/PUT /api/settings`, `POST /api/settings/wazuh/test` |
| Database | status, switch, test, config, purge alerts/incidents |
| Wazuh Queries | CRUD `/api/wazuh-queries` |

---

## 7\. Keamanan

### 7.1 Prinsip desain

1. **Airgapped dan local-first.** Tidak ada panggilan cloud, CDN, tracking, atau telemetri. Satu-satunya model opsional adalah Ollama loopback/LAN.  
2. **Bukti sebelum verdict.** Setiap klasifikasi membawa sinyal dan alasan.  
3. **Tidak ada label "aman".** Status kosong, cached-empty, dan tersamarkan dinamai eksplisit.  
4. **Telemetri mentah tetap lokal.** `full_log`, `raw`, dan `data` tidak masuk prompt, localStorage, analytics, atau URL eksternal.  
5. **Least privilege.** Profil database remote bersifat read-only; aksi destruktif memerlukan pratinjau dan hak admin.

### 7.2 Autentikasi dan otorisasi

- Pengguna disimpan di `wazuh.app_settings` (`auth_users`).  
- Password di-hash **PBKDF2-HMAC-SHA256, 120.000 iterasi**, lalu ciphertext-nya dienkripsi Fernet.  
- Sesi berupa cookie `arbiter_session` berisi klaim terenkripsi (`username`, `role`, `display_name`, `iat`, `exp`), TTL **12 jam**, `HttpOnly`, `SameSite=Lax`.  
- Token juga dapat dikirim via `Authorization: Bearer` atau `X-Arbiter-Token`.  
- Role: `admin` dan `analyst`.  
- Endpoint admin-only: manajemen pengguna, `/api/database/*`, dan perubahan `/api/settings` (GET tetap boleh untuk pengguna login).  
- Middleware menolak `401` bila sesi tidak ada, dan `403` bila role tidak cukup.  
- Admin terakhir tidak dapat dihapus atau diturunkan role-nya; akun yang sedang dipakai tidak dapat menghapus dirinya sendiri.

Kredensial admin awal berasal dari `ARBITER_ADMIN_USER` / `ARBITER_ADMIN_PASSWORD`, dengan default `admin` / `arbiter123`. **Ganti segera setelah instalasi.**

### 7.3 Rahasia saat istirahat

- Password Wazuh Indexer, API key AbuseIPDB, dan URI database remote dienkripsi dengan **Fernet** sebelum disimpan di PostgreSQL.  
- Kunci diambil dengan urutan:  
  1. `ARBITER_SECRET_KEY`  
  2. `ARBITER_SECRET_KEY_FILE`  
  3. file `0600` yang dibuat otomatis di `~/.local/share/arbiter/secret.key` (lokal) atau `/data/secret.key` (Docker, volume `arbiter_secrets`).  
- API tidak pernah mengembalikan rahasia; nilai disamarkan (`***`).  
- Jangan commit kunci atau `.env`.

### 7.4 Isolasi jaringan dan SSRF

- URL Ollama divalidasi: hanya `localhost`, IP loopback, IP privat/link-local, CGNAT, hostname satu-label, atau suffix LAN umum. Skema harus `http`/`https`.  
- URL Wazuh Indexer diisi operator melalui Pengaturan; pola indeks dibatasi karakter aman.  
- Verifikasi TLS Wazuh Indexer aktif secara default (`verify_tls: true`).  
- Remote database profile bersifat **read-only** dan URI tersimpan terenkripsi.  
- AbuseIPDB hanya dipanggil saat pengguna menjalankan enrichment eksplisit.

### 7.5 Perlindungan data dan ekspor

- Redaksi deterministik IP, email, password, token sebelum berbagi.  
- `safe_alerts()` menghapus field mentah sebelum payload menghadap model atau klien triage.  
- Ekspor dibatasi 10.000 alert; kelebihan menghasilkan **413**, bukan file terpotong diam-diam.  
- Purge database memerlukan token pratinjau berumur **60 detik** dan kriteria yang sama persis; token disimpan di registry dengan eviction.  
- Query list dibatasi (contoh: alert default 500, maksimum 10.000; AI 1–5000).

### 7.6 Batasan keamanan yang perlu diketahui

Dokumen ini jujur terhadap implementasi saat ini:

- **Tidak ada rate limiting login** dan **tidak ada token CSRF** eksplisit; cookie mengandalkan `SameSite=Lax` dan pola same-origin.  
- Atribut cookie `Secure` tidak dipasang otomatis. Jika diakses lewat HTTPS, terminasi TLS dan header tambahan perlu disediakan reverse proxy.  
- `PORT=0` mematikan enforcement auth pada middleware; jangan pernah mengekspos mode ini.  
- Tenant **bukan** otorisasi; pemisahan pengguna per tenant tidak ditegakkan.  
- Default admin password harus diganti; default PostgreSQL `PASSWORD_BARU_KUAT` di compose harus diganti untuk produksi.  
- Aplikasi default berjalan HTTP di port 8000\. Untuk jaringan bersama, tempatkan di belakang reverse proxy TLS (`docker/nginx/default.conf` tersedia) dan batasi akses jaringan.

---

## 8\. Instalasi

### 8.1 Prasyarat

- Docker \+ Docker Compose **atau** Python 3.11+ dan PostgreSQL 16+.  
- Port `8000` tersedia.  
- Untuk pengujian frontend: Node.js 18+ (opsional).

>   
> Jika Arbiter sudah berjalan sebagai service systemd (`Arbiter.service`), hentikan dulu karena keduanya memakai port 8000\.

### 8.2 Metode A — Docker standalone (paling cepat)

Cocok untuk pengguna baru yang belum punya PostgreSQL.

```sh
git clone https://github.com/Nothrovo/Arbiter.git
cd Arbiter

cp .env.example .env
```

Sesuaikan `.env` agar menunjuk ke database container standalone:

```
PORT=8000
DATABASE_URL=postgresql://arbiter:PASSWORD_BARU_KUAT@127.0.0.1:5432/arbiter
ARBITER_ADMIN_USER=admin
ARBITER_ADMIN_PASSWORD=ganti-password-ini
ARBITER_SECRET_KEY_FILE=/data/secret.key
```

Jalankan:

```sh
docker compose --profile standalone up -d --build
```

Buka [**http\://localhost:8000**](http://localhost:8000).

Catatan penting:

- Container `db` memakai kredensial `arbiter` / `PASSWORD_BARU_KUAT` / database `arbiter` dari `compose.yaml`. Ganti password tersebut di compose **dan** `.env` untuk penggunaan nyata.  
- Container `db` mempublikasikan port `5432`. Jika host sudah menjalankan PostgreSQL, gunakan Metode B atau hentikan PostgreSQL host agar tidak bentrok.  
- Skema `wazuh.*` dibuat otomatis saat startup melalui `init_database()`; `docker/postgres/init.sql` juga disediakan untuk inisialisasi container.

### 8.3 Metode B — Host mode (PostgreSQL yang sudah ada)

```sh
git clone https://github.com/Nothrovo/Arbiter.git
cd Arbiter

cp .env.example .env
# Edit DATABASE_URL, misalnya:
# DATABASE_URL=postgresql://user:password@127.0.0.1:5432/arbiter

docker compose up -d --build
```

Buka [**http\://localhost:8000**](http://localhost:8000).

Pastikan:

- Database tujuan sudah ada dan dapat diakses dari host.  
- User database memiliki izin membuat schema/tabel (atau jalankan `docker/postgres/init.sql` lebih dulu).  
- `REMOTE_DATABASE_URL` hanya diisi jika memakai database IP Intel eksternal.

Integrasi IP Intel (opsional):

```
REMOTE_DATABASE_URL=postgresql://ip_intel_read_login:CHANGE_ME@127.0.0.1:5433/ip_intel
```

Gunakan login **read-only**. Jangan mengubah port internal PostgreSQL sumber.

### 8.4 Metode C — Python lokal tanpa Docker

```sh
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env             # sesuaikan DATABASE_URL

# Buat database jika belum ada (contoh)
createdb -h 127.0.0.1 -U postgres arbiter

./start.sh
```

`start.sh` memuat `.env`, memakai `.venv` bila tersedia, dan menjalankan Uvicorn dengan `--reload`. Aplikasi tersedia di [**http\://127.0.0.1:8000**](http://127.0.0.1:8000).

Jika ingin skema dibuat eksplisit:

```sh
psql "postgresql://user:password@127.0.0.1:5432/arbiter" \
  -f docker/postgres/init.sql
```

### 8.5 Konfigurasi Wazuh Indexer (opsional, untuk Realtime)

1. Login sebagai admin.  
2. Buka **Pengaturan** (`#/settings`).  
3. Isi:  
   - **URL Indexer**, contoh `https://wazuh.example.local:9200`  
   - **Username** dan **password**  
   - **Pola indeks**, default `wazuh-alerts-*`  
   - **Verifikasi TLS** (biarkan aktif kecuali lab memakai sertifikat self-signed)  
4. Klik **Tes koneksi**.  
5. Aktifkan **Realtime** dengan interval 10–300 detik, mode `interval` atau `daily`, serta batas `max_alerts` dan rentang rule level.

### 8.6 Konfigurasi AI lokal (opsional)

```sh
# Di host yang sama dengan Arbiter
ollama serve
ollama pull qwen2.5:3b
```

Lalu di **Pengaturan → AI**:

- Aktifkan AI lokal.  
- Base URL: `http://127.0.0.1:11434` (loopback/LAN saja).  
- Model: sesuai model yang tersedia.  
- Timeout: 10–180 detik.

Jika Ollama tidak tersedia, Arbiter otomatis memakai rule deterministik dan menandai mode `local_rules_fallback`.

### 8.7 Login pertama

- URL: [**http\://localhost:8000**](http://localhost:8000)  
- Username: `ARBITER_ADMIN_USER` (default `admin`)  
- Password: `ARBITER_ADMIN_PASSWORD` (default `arbiter123`)

Segera buat pengguna analis dan ganti password admin melalui menu pengguna. Minimal 6 karakter; username 3–50 karakter (`A-Z`, `a-z`, `0-9`, `.`, `_`, `-`).

### 8.8 Verifikasi instalasi

```sh
# Liveness
curl -s http://127.0.0.1:8000/health

# Ringkasan workspace (butuh sesi login)
curl -s http://127.0.0.1:8000/api/health

# Uji terisolasi (jangan pakai tests.test_api pada database produksi)
.venv/bin/python -m unittest \
  tests.test_wazuh_intel tests.test_ai_triage tests.test_parser \
  tests.test_exports tests.test_privacy tests.test_dedup \
  tests.test_ui_api tests.test_ui_safety tests.test_settings \
  tests.test_stats tests.test_triage_scope tests.test_database_trust -q

# Frontend (butuh Node 18+)
npm test
```

Checklist manual:

1. Login berhasil.  
2. Impor satu file JSON sintetis di `#/imports`.  
3. Alert muncul di `#/triage` dengan tenant yang benar.  
4. Inspector menampilkan log dan klasifikasi.  
5. Jalankan AI Triage; hasil tersimpan saat halaman dibuka ulang.  
6. Buat insiden dari alert terpilih.  
7. Ekspor DOCX/XLSX dari `#/reports`.

### 8.9 Variabel lingkungan

| Variabel | Default | Fungsi |
| :---- | :---- | :---- |
| `PORT` | `8000` | Port aplikasi |
| `HOST` | `0.0.0.0` | Alamat bind |
| `DATABASE_URL` | `postgresql://nothrovo@127.0.0.1:5432/abuseip` | Database utama |
| `REMOTE_DATABASE_URL` | host IP Intel | Profil remote read-only |
| `ACTIVE_DB_PROFILE` | `local` | Profil database aktif saat start |
| `ARBITER_SECRET_KEY` | kosong (random) | Kunci Fernet eksplisit |
| `ARBITER_SECRET_KEY_FILE` | `~/.local/share/arbiter/secret.key` | Lokasi file kunci |
| `ARBITER_ADMIN_USER` | `admin` | Username admin awal |
| `ARBITER_ADMIN_PASSWORD` | `arbiter123` | Password admin awal |
| `ENABLE_LOCAL_AI` | `false` | Default AI lokal |
| `OLLAMA_BASE_URL` | `http://127.0.0.1:11434` | Endpoint Ollama |
| `OLLAMA_MODEL` | `qwen3.5:9b` | Model Ollama |
| `ABUSEIPDB_API_KEY` | Kosong | Enrichment AbuseIPDB eksplisit |

Jangan commit `.env` atau kunci enkripsi.

---

## 9\. Troubleshooting

| Gejala | Penyebab umum | Penanganan |
| :---- | :---- | :---- |
| `401 Sesi login diperlukan` | Belum login / cookie hilang | Login ulang; pastikan same-origin |
| `403 Fitur hanya untuk Admin` | Role `analyst` | Gunakan akun admin atau minta role dinaikkan |
| Gagal konek database | `DATABASE_URL` salah / DB belum ada | Periksa URI, buat database, cek izin user |
| Standalone DB tidak terpakai | `.env` masih memakai default `nothrovo@.../abuseip` | Set `DATABASE_URL` ke `arbiter:...@127.0.0.1:5432/arbiter` |
| Port 5432 bentrok | PostgreSQL host sudah berjalan | Hentikan salah satu atau pakai Metode B |
| Port 8000 bentrok | `Arbiter.service` aktif | `sudo systemctl stop Arbiter.service` |
| Kredensial tidak bisa didekripsi | Kunci berubah/hilang | Pulihkan file kunci atau isi ulang kredensial |
| Koneksi Wazuh gagal | URL/pola indeks/TLS salah | Tes koneksi di Pengaturan; periksa sertifikat |
| AI selalu fallback | Ollama mati / URL bukan loopback-LAN | Jalankan `ollama serve`; periksa base URL |
| Ekspor 413 | Scope \> 10.000 alert | Persempit filter atau pilih insiden tertentu |
| Grafik kosong | Tenant/filter tidak cocok | Set tenant `Semua tenant` atau reset filter |

---

## 10\. Pengembangan dan Pemeliharaan

```sh
# Backend (suite terisolasi, fixture sintetis)
.venv/bin/python -m unittest tests.test_wazuh_intel tests.test_ai_triage \
  tests.test_parser tests.test_exports tests.test_privacy tests.test_dedup \
  tests.test_ui_api tests.test_ui_safety tests.test_settings \
  tests.test_stats tests.test_triage_scope tests.test_database_trust -q

# Frontend
node --test tests/frontend/*.test.mjs

# Lint design system
npx -y @google/design.md@0.4.0 lint docs/ui-ux-redesign/DESIGN.md
```

Aturan kontribusi penting:

- Jangan menambahkan React/Vue/Angular/Svelte/Tailwind.  
- Jangan menambahkan font CDN, analytics, atau fetch eksternal.  
- Jangan mengakses data produksi atau `.env` saat pengembangan.  
- Jangan menjalankan `tests.test_api` terhadap database aktif.  
- Jangan membuat halaman dashboard overview.  
- Jangan memberi label "Clean", "Aman", atau "Safe".

---

## 11\. Lisensi

Arbiter didistribusikan di bawah **MIT License** (lihat [`README.md`](../README.md#-license)).  
