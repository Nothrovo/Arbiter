# Arsitektur Arbiter — Web & Tools

> Dokumen ini menjelaskan arsitektur teknis Arbiter: gaya arsitektur, diagram
> konteks dan container, struktur web frontend, struktur tools backend, alur
> data, model data, deployment, keamanan, dan batasan operasional.
>
> Berdasarkan implementasi di repositori: `app/main.py`, `app/static/js/`,
> `app/database.py`, dan modul domain lainnya.

Dokumen terkait:

- [`DOKUMENTASI.md`](DOKUMENTASI.md) — ringkasan, workflow, keamanan, instalasi.
- [`ARCHITECTURE.md`](ARCHITECTURE.md) — kontrak data dan kebijakan klasifikasi.
- [`ui-ux-redesign/DESIGN.md`](ui-ux-redesign/DESIGN.md) — arah desain UI.

---

## 1. Gaya Arsitektur

Arbiter adalah **modular monolith lokal**:

- Satu proses FastAPI melayani API dan aset statis frontend.
- Frontend adalah **vanilla JavaScript ES modules** yang dipecah per fitur,
  bukan SPA framework.
- PostgreSQL adalah satu-satunya penyimpanan persisten.
- Semua pemrosesan berat (parsing, dedup, klasifikasi, korelasi) berjalan
  in-process; tidak ada message broker, worker queue, atau cache eksternal.
- Integrasi keluar bersifat opsional dan eksplisit: Wazuh Indexer, Ollama
  loopback/LAN, database IP Intel, dan AbuseIPDB (hanya saat diminta).

### Prinsip yang membentuk arsitektur

| Prinsip | Konsekuensi teknis |
|---|---|
| Airgapped / local-first | Tidak ada CDN, analytics, telemetri; font dan aset lokal |
| Evidence before verdict | Klasifikasi wajib membawa `signals` + `reason` |
| Deterministic first, AI optional | Rule engine selalu tersedia; Ollama hanya penguat |
| Tenant adalah konteks, bukan otorisasi | Scope melekat pada query dan ekspor |
| Bukti mentah tetap lokal | `full_log` tidak masuk prompt/model payload |
| Degradasi aman | Gagal Wazuh/Ollama/remote DB tidak memblokir workspace lokal |
| Tanpa migrasi framework | HTML/CSS/JS native, tanpa build step frontend |

### Konsekuensi yang disadari

- `app/main.py` bersifat **monolitik** (≈2.500 baris, ±70 endpoint); batas modul
  ditegakkan lewat disiplin impor, bukan framework router.
- Tidak ada ORM; SQL ditulis eksplisit di `main.py`, `query.py`, dan
  `database.py`.
- Frontend merender HTML string dengan `esc()`; tidak ada virtual DOM.
- Switching profil database disimpan di memori proses (plus override
  terenkripsi), sehingga **multi-worker Uvicorn tidak disarankan** untuk fitur
  ini.
- Belum ada job queue; ingest dan ekspor berjalan sinkron dalam request.

---

## 2. Diagram Konteks (C4 Level 1)

```mermaid
flowchart TB
    Analyst["Analis SOC<br/>(browser desktop)"]
    Admin["Admin / Operator"]

    subgraph Arbiter["Arbiter"]
        Desk["Investigation Desk<br/>Triage · Insiden · Laporan"]
    end

    Wazuh["Wazuh Manager / Indexer<br/>(OpenSearch API)"]
    PG[("PostgreSQL 16<br/>wazuh.* + ip_intel_cache")]
    Ollama["Ollama lokal<br/>loopback / LAN (opsional)"]
    IntelDB[("Database IP Intel<br/>remote read-only (opsional)")]
    Abuse["AbuseIPDB API<br/>(hanya enrichment eksplisit)"]

    Analyst -->|"HTTPS/HTTP lokal"| Desk
    Admin -->|"HTTPS/HTTP lokal"| Desk

    Desk -->|"baca alert, realtime pull"| Wazuh
    Desk -->|"baca/tulis alert, insiden, setting"| PG
    Desk -->|"HTTP lokal"| Ollama
    Desk -->|"baca cache reputasi"| IntelDB
    Desk -.->|"aksi pengguna"| Abuse
```

**Aktor:** `analyst` (operasional) dan `admin` (pengguna, database, pengaturan).
**Sistem eksternal:** Wazuh Indexer, PostgreSQL, Ollama, IP Intel, AbuseIPDB.

---

## 3. Diagram Container (C4 Level 2)

```mermaid
flowchart LR
    subgraph Client["Browser"]
        Shell["Shell + Hash Router<br/>app.js · router.js"]
        Features["Feature Modules<br/>triage · stats · incidents ·<br/>imports · reports · realtime ·<br/>ai-triage · database · settings"]
        ClientAPI["API Client<br/>fetch same-origin<br/>timeout · abort · error map"]
        Shell --> Features
        Features --> ClientAPI
    end

    subgraph Server["FastAPI Process :8000"]
        MW["Middleware<br/>auth · RBAC · no-cache"]
        Routes["REST API<br/>app/main.py"]
        Domain["Domain Tools<br/>parser · core · wazuh_intel ·<br/>ai_triage · query · intel · privacy"]
        Infra["Infrastructure<br/>database · settings ·<br/>secure_store · auth · exports"]
        Static["StaticFiles<br/>/static"]
        MW --> Routes
        Routes --> Domain
        Routes --> Infra
    end

    subgraph Storage["Persistent"]
        PG[("PostgreSQL<br/>wazuh.alerts<br/>analysis_groups<br/>alert_group_members<br/>app_settings<br/>ip_intel_cache")]
    end

    Wazuh["Wazuh Indexer"]
    Ollama["Ollama"]
    Remote[("Remote IP Intel DB")]

    ClientAPI -->|"JSON / file upload"| MW
    Client -->|"HTML, CSS, JS, font"| Static
    Infra --> PG
    Domain -->|"HTTP"| Wazuh
    Domain -->|"HTTP loopback"| Ollama
    Domain -->|"read-only"| Remote
```

Catatan: server menyajikan `index.html` dan aset; tidak ada server frontend
terpisah dan tidak ada proses build.

---

## 4. Arsitektur Web (Frontend)

### 4.1 Lapisan frontend

```mermaid
flowchart TB
    subgraph Shell["Shell Layer"]
        HTML["index.html<br/>sidebar · utility bar · dialog"]
        APP["app.js<br/>bootstrap · auth gate · tenant · health"]
        ROUTER["router.js<br/>hash route + guard"]
    end

    subgraph State["State Layer (in-memory)"]
        SCOPE["scope.js<br/>normalisasi tenant & query"]
        SELECTION["selection.js<br/>Set ter-scope tenant"]
        NAV["navigation.js<br/>memori query per tujuan"]
        TRIAGE["triage.js<br/>scroll & versi detail"]
        SIDEBAR["sidebar.js<br/>preferensi collapse"]
        WORKSPACE["workspace.js<br/>health probe state"]
    end

    subgraph UI["Shared UI"]
        PRIM["ui/primitives.js<br/>esc · icon · severity · time · empty"]
        CLIENT["api/client.js<br/>request · json · download · copy"]
    end

    subgraph Features["Feature Modules (lazy load)"]
        F1["triage/<br/>model.js · view.js"]
        F2["incidents/<br/>model · render · state · view · workspace"]
        F3["reports/ · imports/ · stats/"]
        F4["ai-triage/ · realtime/ · database/"]
        F5["settings/ · error-codes/ · wazuh-queries/"]
    end

    HTML --> APP
    APP --> ROUTER
    APP --> State
    APP --> UI
    ROUTER -->|"dynamic import"| Features
    Features --> State
    Features --> UI
    Features -->|"fetch /api/*"| CLIENT
```

### 4.2 Pola feature module

Setiap destinasi mengikuti kontrak yang sama:

```js
// features/<page>/view.js
export async function mount(context) {
  // context: { root, route, navigate, selection, notify,
  //            databaseChanged, signal, setGuard }
  // render, pasang listener, fetch data
  return function dispose() {
    // lepas listener/timer yang tidak memakai signal
  };
}
```

- `app.js` melakukan `importFeature(page)` → `./features/<page>/view.js`.
- Jika dynamic import gagal karena cache browser, loader mencoba sekali lagi
  dengan query `?retry=<timestamp>`.
- Setiap navigasi membuat `AbortController` baru; request lama dibatalkan.
- `routeVersion` mencegah feature lama menimpa halaman baru.
- `dispose()` dipanggil saat rute berubah atau login gate ditampilkan.
- `setGuard()` mencegah navigasi saat ada perubahan belum disimpan.

Pemisahan `model.js` / `render.js` / `view.js` / `state.js` membuat logika
turunan, markup, dan efek samping dapat diuji terpisah (`tests/frontend/`).

### 4.3 Routing dan scope

- Hash router: `#/<page>?tenant=a&tenant=b&...`.
- Halaman yang dikenali: `triage`, `stats`, `incidents`, `imports`, `reports`,
  `realtime`, `ai-triage`, `wazuh-queries`, `error-codes`, `database`,
  `settings`.
- Tenant di URL adalah sumber kebenaran scope; `scope.js` menormalkan nilai,
  menghapus pagination yang tidak relevan, dan membangun key scope.
- `selection.js` menolak item dari tenant di luar scope aktif.
- `navigation.js` menyimpan query terakhir per destinasi, sehingga pengguna
  kembali ke filter yang sama.

### 4.4 Alur render satu halaman

```mermaid
sequenceDiagram
    autonumber
    participant U as Analis
    participant R as router.js
    participant A as app.js
    participant L as feature-loader.js
    participant F as features/<page>/view.js
    participant C as api/client.js
    participant S as FastAPI

    U->>R: ubah hash / klik navigasi
    R->>A: onChange(route)
    A->>A: cek auth, guard, scope, scroll memory
    A->>A: abort request & dispose feature lama
    A->>L: importFeature(page)
    L-->>A: module (retry ?retry= jika gagal)
    A->>F: mount(context)
    F->>C: json('/api/...', {signal})
    C->>S: fetch same-origin
    S-->>C: JSON / error
    C-->>F: data
    F->>A: render ke #main-content
    A-->>U: halaman siap
```

### 4.5 Login gate dan hak tampilan

- `app.js` memanggil `/api/auth/me` pada render pertama.
- Jika tidak terautentikasi, sidebar dan utility bar disembunyikan dan form login
  dirender di area konten.
- Menu `database` dan `settings` disembunyikan untuk role `analyst`.
- Ini hanya lapisan UX; server tetap menolak endpoint admin dengan `403`.

### 4.6 State yang tidak dipersistensi

| State | Lokasi | Hilang saat |
|---|---|---|
| Seleksi alert | Memori `Set` | Reload / ganti tenant |
| Scroll triage | Memori `Map` | Reload |
| Filter per tujuan | Memori `navigation.js` | Reload |
| Preferensi sidebar | `localStorage` | Dibersihkan pengguna |
| Tema | `localStorage` | Dibersihkan pengguna |
| Hasil AI Triage | PostgreSQL (`app_settings`) | Tidak hilang |
| Sesi login | Cookie terenkripsi | 12 jam / logout |

---

## 5. Arsitektur Tools (Backend)

### 5.1 Peta modul dan dependensi

```mermaid
flowchart TB
    subgraph API["API / Transport — main.py"]
        EP["±70 endpoint REST"]
        MW["Middleware auth + no-cache"]
        LIFE["Lifespan: init_database, migrate_settings"]
    end

    subgraph Domain["Domain Tools"]
        PARSE["parser.py<br/>parse_export · regex dissector · signature"]
        CORE["core.py<br/>normalize_alert · suggest_groups · Ollama"]
        INTELIG["wazuh_intel.py<br/>classify_alert · correlate_alerts ·<br/>build_attack_chains"]
        AIT["ai_triage.py<br/>cluster · fallback · window WIB · lock_tp"]
        QUERY["query.py<br/>alert_where · facet · malicious spotter"]
        PRIV["privacy.py<br/>sanitize_text"]
        EXPORT["exports.py<br/>HTML · DOCX · XLSX · TSV · MD"]
        INTEL["intel.py<br/>cache · AbuseIPDB · remote sync"]
    end

    subgraph Infra["Infrastructure"]
        DB["database.py<br/>schema · dedup · profile · purge"]
        SET["settings.py<br/>Wazuh · realtime · AI · intel"]
        SEC["secure_store.py<br/>Fernet"]
        AUTH["auth.py<br/>PBKDF2 · sesi · role"]
    end

    subgraph External["External"]
        WZ["Wazuh Indexer"]
        OL["Ollama"]
        PG[("PostgreSQL")]
        AB["AbuseIPDB"]
    end

    MW --> EP
    EP --> PARSE
    EP --> CORE
    EP --> INTELIG
    EP --> AIT
    EP --> QUERY
    EP --> PRIV
    EP --> EXPORT
    EP --> INTEL
    EP --> DB
    EP --> SET
    EP --> AUTH

    PARSE --> CORE
    CORE --> INTELIG
    INTELIG --> AIT
    AIT --> CORE
    CORE --> SEC
    SET --> SEC
    AUTH --> SEC
    SET --> WZ
    AIT --> OL
    CORE --> OL
    INTEL --> AB
    DB --> PG
    SET --> PG
    AUTH --> PG
```

### 5.2 Tanggung jawab per modul

| Modul | Peran arsitektural | Tidak bertanggung jawab atas |
|---|---|---|
| `main.py` | Kontrak HTTP, orkestrasi, validasi input, otorisasi endpoint | Algoritma klasifikasi |
| `parser.py` | Ekstraksi teks/log menjadi struktur | Penentuan verdict |
| `core.py` | Normalisasi alert + signature + grouping dasar | Kebijakan rule kuratif |
| `wazuh_intel.py` | Kebijakan verdict, role, priority, korelasi, chain | Penyimpanan |
| `ai_triage.py` | Clustering, fallback rule, window WIB, sanitasi payload | Memanggil DB langsung |
| `query.py` | SQL filter tenant/time/facet/preset | Menjalankan query |
| `database.py` | Koneksi, skema, dedup upsert, profil, purge | Semantik klasifikasi |
| `settings.py` | Validasi dan penyimpanan konfigurasi Wazuh/AI/intel | Deteksi alert |
| `auth.py` | Kredensial, sesi, role | Otorisasi per-resource |
| `secure_store.py` | Enkripsi/dekripsi lokal | Manajemen kunci terpusat |
| `intel.py` | Reputasi IP dan sinkronisasi cache | Klaim "aman" |
| `privacy.py` | Redaksi deterministik | Jaminan anonimisasi |
| `exports.py` | Format deliverable | Penentuan scope ekspor |

### 5.3 Lapisan request

```mermaid
sequenceDiagram
    autonumber
    participant B as Browser
    participant M as Middleware
    participant H as Endpoint main.py
    participant D as get_db()
    participant X as Modul domain
    participant P as PostgreSQL

    B->>M: HTTP /api/*
    alt path bukan publik
        M->>M: baca cookie / Bearer / X-Arbiter-Token
        M->>M: verify_session_token (Fernet + exp)
        alt token invalid
            M-->>B: 401
        else role tidak cukup untuk endpoint admin
            M-->>B: 403
        else valid
            M->>M: request.state.user
        end
    end
    M->>H: teruskan request
    H->>H: validasi parameter (tenant, limit, ID)
    H->>D: context manager koneksi
    D->>P: psycopg.connect(profile aktif)
    H->>X: panggil fungsi domain
    X-->>H: hasil / HTTPException
    H->>P: SELECT / INSERT / UPDATE
    H-->>B: JSON / file / 4xx
    D->>P: commit / rollback / close
```

Middleware hanya mengautentikasi jalur `/api/*`. `index.html` dan `/static/*`
tidak memerlukan sesi; data tetap tidak dapat diambil tanpa token API.

### 5.4 Alur ingest end-to-end

```mermaid
sequenceDiagram
    autonumber
    participant U as Analis
    participant API as main.py
    participant P as parser.py
    participant C as core.py
    participant W as wazuh_intel.py
    participant DB as database.py
    participant PG as PostgreSQL

    U->>API: POST /api/import (file) atau /api/import-text
    API->>P: parse_export(content)
    P-->>API: alerts[] + errors[]
    loop setiap alert
        API->>C: normalize_alert(raw)
        C->>C: tenant, agent, rule, source_ip,<br/>parsed_details, signature
        C->>W: classify_alert(normalized)
        W-->>C: verdict, role, priority,<br/>confidence, signals, origin
        C-->>API: alert ternormalisasi
        API->>DB: ingest_alert_with_dedup(conn, alert)
        DB->>PG: INSERT ... ON CONFLICT / update hit_count
        DB-->>API: (inserted, deduplicated)
    end
    API-->>U: ringkasan impor + error
```

Dedup menggunakan signature stabil; alert berulang menambah `hit_count` dan
memperluas `last_seen`, bukan membuat baris baru.

### 5.5 Alur korelasi dan sugesti

1. `GET /api/suggestions` mengambil alert dalam scope (maksimum 300).
2. `correlate_alerts()` menautkan respons aktif ke origin.
3. Grup kanonik dibentuk dari `(agent_name, rule_id)` → `log_signature` →
   `(source_ip, rule_id)`.
4. `build_attack_chains()` menyusun urutan lintas rule per host+IP.
5. `suggestions_with_fallback()` memakai Ollama hanya jika diaktifkan dan
   tersedia; jika gagal, hasil deterministik tetap dikembalikan.

### 5.6 Alur AI Triage

```mermaid
sequenceDiagram
    autonumber
    participant U as Analis
    participant API as main.py
    participant AI as ai_triage.py
    participant OL as Ollama (opsional)
    participant PG as app_settings

    U->>API: POST /api/ai/triage {tenant, limit, group_by, ...}
    API->>PG: baca state window terakhir
    API->>API: query alert sesuai scope + severity band
    API->>AI: safe_alerts(alerts) — buang raw/full_log/data
    AI->>AI: partition per tenant
    AI->>AI: cluster by rule_description / host_rule
    alt AI aktif dan reachable
        AI->>OL: prompt cluster tanpa raw log / alert ID
        OL-->>AI: verdict per cluster
    else AI mati / tidak diaktifkan
        AI->>AI: heuristic_triage (local_rules)
    end
    AI->>AI: lock_tp untuk indikator exploit
    AI->>AI: merge dengan grup window 17:00 WIB
    AI-->>API: groups + mode + window
    API->>PG: simpan state
    API-->>U: hasil triage
```

Guardrail penting:

- Satu grup tidak boleh mencampur dua tenant.
- `lock_tp` mengunci true-positive jika ada indikator exploit terverifikasi.
- Model tidak menerima raw log, `data`, `full_log`, atau alert ID.
- Hasil disimpan agar bertahan antar sesi; window harian memakai UTC+7.

### 5.7 Alur ekspor

```mermaid
flowchart LR
    Q["Query param scope<br/>tenant, filter, preset,<br/>incident/group, alert_ids"] --> S["export_scope()<br/>normalisasi + buang pagination"]
    S --> F{"Format"}
    F -->|HTML| H["generate_gdocs_html_report"]
    F -->|DOCX| D["generate_docx_landscape_report"]
    F -->|XLSX| X["generate_xlsx_workbook"]
    F -->|TSV| T["generate_tsv_table"]
    F -->|Markdown| M["generate_markdown_report"]
    F -->|CSV| C["csv.writer (main.py)"]
    H --> B["Response / StreamingResponse"]
    D --> B
    X --> B
    T --> B
    M --> B
    C --> B
    S -->|"> 10.000 alert"| E["HTTP 413<br/>tidak ada file parsial"]
```

Semua format menerima **filter yang sama**; `scopeParams()` di frontend dan
`export_scope()` di backend menormalkan scope, sehingga preview dan hasil unduhan
konsisten.

### 5.8 Profil database dan pemeliharaan

- Dua profil: `local` (read-write) dan `remote` (read-only).
- Profil aktif adalah variabel proses; override URI remote disimpan terenkripsi
  di `app_settings`.
- `get_db()` selalu memakai profil aktif saat koneksi dibuat.
- Purge alert/insiden:
  1. `dry_run` menghitung jumlah dan mengembalikan `preview_token` (TTL 60 detik).
  2. Eksekusi wajib mengirim token dan kriteria identik.
  3. Profil read-only ditolak `403`; perubahan profil di tengah proses ditolak
     `409`.

---

## 6. Arsitektur Data

### 6.1 ERD

```mermaid
erDiagram
    WAZUH_ALERTS {
        bigserial id PK
        text alert_id
        text timestamp
        text tenant
        text agent_name
        text agent_ip
        text rule_id
        int rule_level
        text description
        jsonb rule_groups
        text source_ip
        jsonb data
        jsonb raw
        text log_signature
        int hit_count
        text first_seen
        text last_seen
        jsonb wazuh_ids
        jsonb duplicate_instances
        jsonb parsed_details
        boolean is_reviewed
        timestamptz reviewed_at
        text reviewer_notes
    }

    ANALYSIS_GROUPS {
        uuid id PK
        text title
        text category
        text analysis
        text conclusion
        text recommendation
        text status
        text severity
        text source
        text verdict
        timestamptz created_at
        timestamptz updated_at
    }

    ALERT_GROUP_MEMBERS {
        bigint alert_pk FK
        uuid group_id FK
    }

    APP_SETTINGS {
        text key PK
        jsonb value
        timestamptz updated_at
    }

    IP_INTEL_CACHE {
        text ip PK
        int abuse_score
        int vt_malicious
        text country_code
        text isp
        text_array attack_types
        int total_alert_count
        timestamptz last_seen
    }

    WAZUH_ALERTS ||--o{ ALERT_GROUP_MEMBERS : "alert_pk"
    ANALYSIS_GROUPS ||--o{ ALERT_GROUP_MEMBERS : "group_id"
```

### 6.2 Penyimpanan JSONB

`parsed_details` menyimpan metadata turunan, termasuk
`parsed_details.wazuh_intel` (verdict, role, priority, confidence, signals,
origin, origin_verdict). Ini membuat evolusi klasifikasi tidak memerlukan
migrasi kolom.

Keuntungan: fleksibel dan cepat untuk baseline.
Konsekuensi: query analitik atas field turunan memerlukan indeks ekspresi
(contoh `parsed_details->>'status'`) atau ekstraksi kolom di masa depan.

### 6.3 Indeks

Indeks utama mencakup `source_ip`, `rule_id`, `timestamp`, `tenant`,
`(tenant, log_signature)`, `is_reviewed`, `(tenant, timestamp)`, `rule_level`,
`agent_name`, dan `parsed_details->>'status'`. Dimensi berkardinalitas tinggi
seperti user agent dan URL sengaja tidak diindeks luas untuk mencegah bloat.

### 6.4 Kepemilikan data

| Data | Lokasi | Sifat |
|---|---|---|
| Alert & bukti mentah | `wazuh.alerts` | Sensitif, lokal |
| Kasus & narasi | `wazuh.analysis_groups` | Sensitif, lokal |
| Relasi bukti | `wazuh.alert_group_members` | Lokal |
| Pengaturan & pengguna | `wazuh.app_settings` | Sebagian terenkripsi |
| Cache reputasi | `public.ip_intel_cache` | Lokal / remote read-only |
| Kunci enkripsi | File `0600` di luar repo | Paling sensitif |

---

## 7. Arsitektur Keamanan

### 7.1 Trust boundary

```mermaid
flowchart TB
    subgraph Z1["Zona publik / jaringan kantor"]
        BR["Browser analis"]
    end

    subgraph Z2["Host Arbiter"]
        APP["FastAPI :8000"]
        PG[("PostgreSQL")]
        KEY["File kunci 0600"]
        APP --> PG
        APP --> KEY
    end

    subgraph Z3["Layanan internal"]
        WZ["Wazuh Indexer"]
        OL["Ollama loopback/LAN"]
        IDB[("IP Intel DB read-only")]
    end

    EXT["AbuseIPDB"]

    BR -->|"cookie HttpOnly / Bearer"| APP
    APP -->|"HTTPS / TLS"| WZ
    APP -->|"HTTP lokal"| OL
    APP -->|"read-only"| IDB
    APP -.->|"hanya aksi eksplisit"| EXT
```

### 7.2 Kontrol keamanan per lapisan

| Lapisan | Kontrol |
|---|---|
| Transport | HTTP lokal; TLS via reverse proxy `docker/nginx/default.conf` |
| Autentikasi | PBKDF2-HMAC-SHA256 120k + sesi Fernet 12 jam |
| Otorisasi | Role `admin` / `analyst`; endpoint admin dicek di middleware |
| Rahasia | Fernet at-rest; kunci dari env/file `0600` di luar repo |
| Input | Validasi tenant, limit, ID grup, pola indeks, URL Ollama |
| SSRF | Ollama hanya loopback/privat/LAN; URL Wazuh diisi operator |
| Data | `safe_alerts()` membuang field mentah sebelum model |
| Ekspor | Scope konsisten + batas 10.000 + `413` eksplisit |
| Destruktif | Preview token 60 detik + kecocokan kriteria + profil read-only |
| Frontend | `esc()` pada semua interpolasi; fetch same-origin; tanpa CDN |
| Privasi | Redaksi deterministik; tanpa klaim "aman" |

### 7.3 Batas yang harus dijaga saat deployment

- Jangan ekspos `PORT=0` (middleware tidak menegakkan auth).
- Ganti password admin awal dan password PostgreSQL default.
- Tempatkan di belakang TLS jika diakses dari jaringan bersama.
- Batasi akses jaringan ke port 8000 dan PostgreSQL.
- `network_mode: host` menghilangkan isolasi jaringan container.
- Profil database disimpan per proses; hindari banyak worker Uvicorn.
- Tenant bukan kontrol otorisasi; jangan jadikan batas keamanan antar tim.

---

## 8. Deployment

### 8.1 Topologi A — Docker standalone

```mermaid
flowchart LR
    U["Browser"] -->|":8000"| A["Container arbiter<br/>network_mode: host"]
    A -->|"127.0.0.1:5432"| D[("Container arbiter-db<br/>postgres:16-alpine")]
    A --> V[("Volume arbiter_secrets<br/>/data/secret.key")]
    D --> DV[("Volume arbiter_pgdata")]
    A -->|"HTTPS"| W["Wazuh Indexer"]
```

Perintah: `docker compose --profile standalone up -d --build`.

Prasyarat: port 5432 tidak dipakai PostgreSQL host; `DATABASE_URL` harus
menunjuk `arbiter@127.0.0.1:5432/arbiter`.

### 8.2 Topologi B — Host mode

```mermaid
flowchart LR
    U["Browser"] -->|":8000"| A["Container arbiter<br/>host network"]
    A -->|"127.0.0.1:5432"| P[("PostgreSQL host<br/>sudah ada")]
    A --> V[("Volume arbiter_secrets")]
    A --> R[("Remote IP Intel<br/>read-only, opsional")]
```

Perintah: `docker compose up -d --build`.

### 8.3 Topologi C — Python lokal

```mermaid
flowchart LR
    U["Browser"] -->|":8000"| UV["Uvicorn --reload<br/>app.main:app"]
    UV --> P[("PostgreSQL host")]
    UV --> F["app/static<br/>disajikan langsung"]
    UV --> K["~/.local/share/arbiter/secret.key"]
```

Perintah: `python -m venv .venv`, `pip install -r requirements.txt`,
`./start.sh`.

### 8.4 Topologi D — Reverse proxy TLS

```mermaid
flowchart LR
    U["Browser"] -->|"HTTPS :443"| N["nginx<br/>TLS termination"]
    N -->|"proxy_pass :8000"| A["Arbiter"]
    A --> P[("PostgreSQL")]
```

Template tersedia di `docker/nginx/default.conf`. Cookie sesi saat ini tidak
memasang atribut `Secure`; jika memakai HTTPS, pertimbangkan penyesuaian di
reverse proxy/aplikasi.

### 8.5 Startup sequence

```mermaid
sequenceDiagram
    participant C as Container / start.sh
    participant U as Uvicorn
    participant L as lifespan
    participant DB as database.py
    participant S as settings.py

    C->>U: uvicorn app.main:app
    U->>L: startup
    L->>DB: init_database()
    DB->>DB: CREATE SCHEMA/TABLE/INDEX IF NOT EXISTS
    L->>S: migrate_settings(conn)
    S-->>L: enkripsi kredensial legacy (best effort)
    L-->>U: aplikasi siap
    U-->>C: listen :8000
```

Startup tidak gagal jika migrasi legacy gagal; workspace tetap dapat dibuka.

---

## 9. Alur Realtime

```mermaid
sequenceDiagram
    autonumber
    participant UI as #/realtime
    participant API as main.py
    participant S as settings.py
    participant W as Wazuh Indexer
    participant DB as database.py

    UI->>API: GET /api/realtime/count
    API->>S: load_settings + wazuh_search
    S->>W: query index pattern + rule level
    W-->>S: hits total
    S-->>API: count
    API-->>UI: jumlah alert

    UI->>API: POST /api/realtime/pull {limit, ...}
    API->>S: wazuh_search(...)
    S->>W: search alert
    W-->>S: dokumen alert
    API->>DB: parse + normalize + dedup ingest
    DB-->>API: jumlah baru / duplikat
    API-->>UI: ringkasan pull
```

Realtime tidak memakai daemon terpisah; penjadwalan bersifat pull dari UI/API
sesuai interval pengaturan.

---

## 10. Failure Modes dan Degradasi

| Komponen gagal | Perilaku arsitektur |
|---|---|
| PostgreSQL mati | `503` dengan nama profil; UI menampilkan error, bukan data palsu |
| Wazuh Indexer tidak terjangkau | Impor manual tetap bekerja; realtime menampilkan error |
| Ollama mati | AI Triage memakai `local_rules` / `local_rules_fallback` |
| Remote IP Intel mati | Intel kosong ditampilkan "Belum ada cache"; triage tetap jalan |
| Kunci enkripsi hilang | Kredensial tersimpan tidak dapat didekripsi; isi ulang |
| Respons detail usang | Version guard frontend membuang respons lama |
| Export > 10.000 | `413` eksplisit; tidak ada file parsial |
| Dynamic import gagal | Retry sekali dengan URL baru |
| Navigasi dengan perubahan | Guard meminta konfirmasi sebelum meninggalkan halaman |
| Database switch saat purge | `409`; operasi dibatalkan |

---

## 11. Keputusan Arsitektur dan Trade-off

| Keputusan | Alasan | Trade-off |
|---|---|---|
| Modular monolith | Sederhana, mudah di-deploy airgapped, tanpa infrastruktur tambahan | `main.py` besar; batas modul tidak dipaksakan compiler |
| Vanilla JS + hash router | Tanpa build step, cocok untuk lingkungan tertutup | Tidak ada reaktivitas framework; state dikelola manual |
| SQL eksplisit tanpa ORM | Kontrol penuh atas filter tenant/facet dan performa | Duplikasi SQL dan risiko injection harus dijaga manual |
| JSONB `parsed_details` | Evolusi klasifikasi tanpa migrasi | Query turunan perlu indeks ekspresi |
| Rule deterministik + AI opsional | Auditabilitas dan ketersediaan | AI bukan sumber kebenaran; hasil bisa konservatif |
| Profil DB di memori proses | Switching cepat tanpa restart | Tidak aman untuk multi-worker |
| `network_mode: host` | Mudah terhubung ke PostgreSQL/Wazuh host | Isolasi jaringan container hilang |
| Tenant sebagai konteks | Fleksibel untuk analis lintas tenant | Bukan kontrol otorisasi |
| Ekspor sinkron | Implementasi sederhana dan konsisten | Request panjang untuk data besar; batas 10.000 |

---

## 12. Batas Skalabilitas

- **Ingest:** satu request memproses seluruh file secara berurutan; file sangat
  besar memperpanjang response. Belum ada streaming/queue.
- **Triage:** list default 500, maksimum 10.000; korelasi maksimum 300 alert
  terbaru.
- **AI:** maksimum 5.000 alert per permintaan; model lokal menentukan latency.
- **Ekspor:** 10.000 alert per file.
- **Database:** query difilter tenant dan diindeks; volume sangat besar
  sebaiknya dipartisi per waktu di PostgreSQL.
- **Multi-worker:** hindari selama profil database masih global per proses.
- **Frontend:** seluruh HTML dirender di klien; halaman dengan ribuan baris
  membutuhkan pagination (sudah diterapkan).

---

## 13. Peta Direktori Arsitektural

```text
app/
├── main.py                  # API + middleware + orkestrasi
├── parser.py                # Ekstraksi log
├── core.py                  # Normalisasi + dedup signature + grouping
├── wazuh_intel.py           # Klasifikasi + korelasi + chain
├── ai_triage.py             # AI/heuristik + window WIB
├── query.py                 # Filter SQL + facet + spotter
├── database.py              # Skema + koneksi + profil + purge
├── settings.py              # Konfigurasi Wazuh/AI/intel
├── secure_store.py          # Fernet
├── auth.py                  # Pengguna + sesi + role
├── intel.py                 # Reputasi IP
├── privacy.py               # Redaksi
├── exports.py               # Deliverable
├── index.html               # Shell
└── static/
    ├── fonts/               # IBM Plex lokal
    ├── styles/              # tokens · themes · base · shell · components · ledger
    └── js/
        ├── app.js           # Bootstrap + auth gate + tenant
        ├── router.js        # Hash router
        ├── feature-loader.js
        ├── api/client.js
        ├── ui/primitives.js
        ├── state/           # scope · selection · navigation · triage · sidebar · workspace
        └── features/        # 11 modul destinasi
```

---

## 14. Cara Memverifikasi Arsitektur

```bash
# 1. Kontrak API interaktif (saat aplikasi berjalan)
open http://127.0.0.1:8000/docs

# 2. Health
curl -s http://127.0.0.1:8000/health

# 3. Uji domain tanpa database produksi
.venv/bin/python -m unittest \
  tests.test_wazuh_intel tests.test_ai_triage tests.test_parser \
  tests.test_exports tests.test_privacy tests.test_dedup \
  tests.test_ui_api tests.test_ui_safety tests.test_settings \
  tests.test_stats tests.test_triage_scope tests.test_database_trust -q

# 4. Uji frontend
npm test
```

Pemetaan pengujian ke arsitektur:

| Suite | Lapisan yang diverifikasi |
|---|---|
| `test_parser` | Ekstraksi & signature |
| `test_wazuh_intel` | Klasifikasi, korelasi, chain |
| `test_ai_triage` | Clustering, sanitasi payload, window |
| `test_dedup` | Upsert & hit count |
| `test_ui_api` | Scope tenant & detail guard |
| `test_ui_safety` | Tidak ada markup/XSS berbahaya |
| `test_privacy` | Tidak ada kebocoran telemetri |
| `test_settings` | Validasi endpoint & kredensial |
| `test_database_trust` | Profil, purge, preview token |
| `tests/frontend/*` | Router, state, selection, render |

---

## 15. Ringkasan Arsitektur

```text
┌──────────────────────────── Browser ────────────────────────────┐
│ index.html → app.js → router.js → feature/<page>/view.js        │
│        state/ (scope, selection, navigation, triage)            │
│        ui/primitives.js + api/client.js (same-origin fetch)     │
└───────────────────────────────┬─────────────────────────────────┘
                                │ JSON / file / cookie sesi
┌───────────────────────────────▼─────────────────────────────────┐
│ FastAPI :8000                                                   │
│ middleware auth/RBAC → main.py (API) → domain tools             │
│ parser → core → wazuh_intel → ai_triage → query/intel/privacy   │
│ infrastructure: database · settings · secure_store · auth       │
│ exports: HTML · DOCX · XLSX · TSV · Markdown · CSV              │
└───────────────┬───────────────────────────────┬─────────────────┘
                │                               │
        PostgreSQL 16                    Layanan lokal opsional
   wazuh.alerts / analysis_groups         Wazuh Indexer
   alert_group_members / app_settings     Ollama loopback/LAN
   ip_intel_cache                         IP Intel remote (RO)
```

Inti arsitekturnya: **frontend modular tanpa build step, backend monolit modular
dengan tool deterministik, PostgreSQL sebagai sumber kebenaran, dan semua
integrasi eksternal bersifat opsional serta terbatas pada jaringan lokal.**
