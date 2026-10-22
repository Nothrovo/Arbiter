# Arbiter UI/UX Redesign — Quiet Evidence Desk

**Status: Implemented.** Modular frontend sudah terpasang dan teruji di synthetic environment.

## Ringkasan Perubahan

UI monolitik 1.490-baris (`index.html` asli) dirombak total menjadi arsitektur modular empat destinasi: **Triage → Insiden → Impor → Laporan**. Halaman depan tidak lagi menumpuk semua kontrol; setiap fitur punya route dan modul sendiri.

### Sebelum vs Sesudah

| Metrik | Sebelum | Sesudah |
|--------|---------|---------|
| Kontrol sebelum tabel | 24 | 0 (sidebar nav + scoped toolbar) |
| Baris HTML shell | ~1.490 | 64 |
| JS modules | 1 monolith | 22 ES modules |
| CSS files | 1 inline | 4 token-driven sheets |
| Heuristic score | 19/40 | — (structural issues resolved) |
| First data row (desktop) | ~395px dari top | ~211px dari top |
| Mobile horizontal overflow | Ada | Tidak ada (320px verified) |

## Arsitektur yang Terpasang

```
app/
├── index.html                    # Shell 64-baris, semantic landmarks
├── static/
│   ├── fonts/                    # IBM Plex Sans/Mono (OFL, lokal)
│   ├── styles/
│   │   ├── tokens.css            # Design token CSS custom properties
│   │   ├── base.css              # Reset, typography
│   │   ├── shell.css             # Sidebar, workspace grid, responsive
│   │   └── components.css        # Panel, toolbar, table, inspector, dialog
│   └── js/
│       ├── app.js                # Shell controller, router, tenant, health
│       ├── router.js             # Hash router (#/triage, #/incidents/:id, …)
│       ├── api/client.js         # Same-origin API client, timeout, error
│       ├── state/
│       │   ├── scope.js          # Query normalization, export scope
│       │   ├── selection.js      # Tenant-scoped selection store
│       │   ├── triage.js         # Queue scroll memory, detail version
│       │   ├── navigation.js     # Cross-page query memory
│       │   └── workspace.js      # Health probe
│       ├── ui/primitives.js      # esc(), icon(), severity(), formatTime()
│       └── features/
│           ├── triage/           # model.js, view.js
│           ├── incidents/        # model.js, render.js, state.js, view.js, workspace.js
│           ├── imports/          # model.js, render.js, view.js
│           └── reports/          # model.js, render.js, view.js
```

## Deliverable Desain

1. [AUDIT.md](AUDIT.md) — bukti masalah asli, skor heuristik 19/40, source locations.
2. [BLUEPRINT.md](BLUEPRINT.md) — sitemap, wireframe teks, module architecture, phase plan.
3. [DESIGN.md](DESIGN.md) — Quiet Evidence Desk: token spec, typography, color, layout, motion.
4. [IMPLEMENTATION-CONTRACT.md](IMPLEMENTATION-CONTRACT.md) — kontrak API dan modul untuk implementasi.
5. [tokens.json](tokens.json) / [tokens.css](tokens.css) — DTCG dan CSS custom-property export.

## Test Coverage

| Suite | Tests | Status |
|-------|-------|--------|
| Frontend (Node `--test`) | 44 | ✅ Pass |
| Backend (unittest) | 61 | ✅ Pass |
| JS syntax check | 22 modules | ✅ 0 errors |
| Impeccable detector | source scan | ✅ 0 findings |
| DESIGN.md lint | @google/design.md | ✅ 0 errors, 2 warnings |

## Evidence

### Audit (sebelum)
- `evidence/before-1280.png` — screenshot UI asli pada isolated fixture.
- `evidence/before-mobile.png` — mobile screenshot.
- `evidence/baseline-1280.json` — parent geometry (banner 31px, 24 kontrol).
- `evidence/baseline-responsive.json` — responsive geometry.
- `evidence/reviewer-b-report.json` — independent technical audit.
- `evidence/detector-findings.json` — AI slop detector findings (25 occurrences).

### Implementasi (sesudah)
- `implementation-evidence/triage-desktop.png` — triage queue 1440px.
- `implementation-evidence/triage-mobile.png` — triage queue mobile.
- `implementation-evidence/incident-desktop.png` — case editor 1440px.
- `implementation-evidence/responsive-triage.json` — CDP geometry measurements.
- `implementation-evidence/route-geometry.json` — all routes × 3 viewports, 0 overflow.

## Keputusan Arsitektur Kunci

1. **Hash router** — `#/triage`, `#/incidents/:id`, `#/imports`, `#/reports`. SPA tanpa server route config.
2. **Selection as state** — `selectedIds` di JS Set, bukan DOM checkboxes. Survives rerender, tenant-guarded.
3. **Export scope consistency** — `scopeParams()` strips pagination, enforces filter parity untuk semua format.
4. **Intel labels** — "Belum ada cache" / "Tidak ada deteksi" / scored. Tidak pernah "Clean" atau "Aman".
5. **Scoped empty case rejection** — Case tenant-scoped tanpa evidence ditolak sebelum mutasi.
6. **Detail version guard** — Stale API responses dari inspector sebelumnya di-discard via monotonic counter.

## Batas dan Catatan

- Semua pengujian menggunakan data sintetis. Tidak ada database SGU, .env, alert asli, atau log produksi yang diakses.
- Font IBM Plex di-host lokal (OFL license). Tidak ada CDN, analytics, atau external fetch.
- Browser QA dilakukan di synthetic server (port 8767), bukan production (port 8000).
- Populated workflows, security enforcement, dan volume performance belum diuji di production.
