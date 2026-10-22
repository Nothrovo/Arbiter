# MANUAL — Menjalankan IP Intel Web

Panduan lokal (Windows + Docker Desktop). Semua perintah dijalankan di PowerShell
dari folder `C:\Users\HETSHI\Downloads\data`.

## 1. Cara cepat (otomatis)

```powershell
.\start-web.ps1    # cek docker + pg-fwd, lalu jalankan web di background
.\stop-web.ps1     # hentikan web
```

Lalu buka:
- Tabel utama : http://127.0.0.1:8898/
- Batch search: http://127.0.0.1:8898/batch
- Contoh detail: http://127.0.0.1:8898/ip/54.209.60.63
- Graph proyek : buka file `ipintel/docs/graph.html` di browser

## 2. Cara manual (langkah per langkah)

1. **Pastikan Docker jalan** (Docker Desktop hijau). Cek:
   ```powershell
   docker ps --format "{{.Names}} {{.Status}}"
   ```
   Wajib ada: `postgres-ticache`, `n8n`, dan **`pg-fwd`**.
   Kalau `pg-fwd` hilang (mis. setelah reinstall), buat ulang:
   ```powershell
   docker run -d --name pg-fwd --network soc-net -p 127.0.0.1:5433:5432 --restart unless-stopped alpine:latest sh -c "apk add --no-cache socat >/dev/null 2>&1 && socat TCP-LISTEN:5432,fork,reuseaddr TCP:postgres-ticache:5432"
   ```

2. **Jalankan web** (background, log ke `web.log`):
   ```powershell
   Start-Process -FilePath "python3" -ArgumentList "ipintel/app.py" `
     -RedirectStandardOutput "web.log" -RedirectStandardError "web.err.log" `
     -WindowStyle Hidden -WorkingDirectory "C:\Users\HETSHI\Downloads\data"
   ```

3. **Cek kesehatan**:
   ```powershell
   Invoke-WebRequest http://127.0.0.1:8898/api/health -UseBasicParsing | Select-Object -Expand Content
   # harus: {"ok":true}
   ```

4. **Hentikan web**:
   ```powershell
   .\stop-web.ps1
   # atau manual:
   Get-CimInstance Win32_Process -Filter "Name='python3.exe'" |
     Where-Object { $_.CommandLine -match "app.py" } |
     ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
   ```

## 3. Fitur web

| Halaman | Fungsi |
|---|---|
| `/` | Tabel + search (IP/ISP/ASN/kota/negara/domain), filter skor & versi IP, pagination 100/halaman, tombol **Scan update skor basi** |
| `/batch` | Paste/upload CSV → akuntansi token → checkbox → **salin `data.srcip: ("a" OR "b")`**; tombol scan Cepat/Lengkap + progress per tahap |
| `/ip/<ip>` | Detail + raw JSON AbuseIPDB/geo |
| `/api/enrich` | Dipakai n8n (DB-first). Lihat contoh node di chat |
| `/api/queue` | Status antrean background (JSON) |
| `/api/update` | Antrekan update skor basi: `POST {"max_age_days":7}` |
| `/api/health` | Cek hidup |

## 4. Utilitas CLI (`ipintel/`)

| Perintah | Fungsi |
|---|---|
| `python3 ipintel/scan.py` | Scan CSV no-cloudflare (skip yg sudah ada) |
| `python3 ipintel/scan.py --only 1.2.3.4` | Scan 1 IP |
| `python3 ipintel/scan.py --refresh` | Scan ulang semua |
| `python3 ipintel/test_gsd.py` | Matrix 11 skenario enrichment (harus 11/11 PASS) |
| `python3 ipintel/graphify_project.py` | Regenerasi `docs/` setelah ubah kode |
| `python3 ipintel/db.py` | Migrasi skema (idempotent) |

## 5. Troubleshooting

| Gejala | Penyebab umum | Solusi |
|---|---|---|
| Browser tidak bisa buka 8898 | Proses Flask mati (mis. PC restart) | Jalankan `.\start-web.ps1` |
| `/api/enrich` error koneksi DB | `pg-fwd` mati | Buat ulang (langkah 2.1) |
| Scan batch lambat/ETA besar | Throttle AbuseIPDB (normal) | Pakai mode **Cepat**, detail menyusul background |
| Skor 0 tidak tampil | Filter default skor ≥ 1 | Set Skor 0–100 |
| IP tidak ketemu padahal ada | Cek baris "di luar range" / "terfilter versi" / invalid | Lebarkan range, versi = all |

## 6. File penting

- `ipintel/app.py` — web Flask (port 8898)
- `ipintel/scan.py` — logika enrichment (AbuseIPDB + geo berlapis)
- `ipintel/worker.py` — worker background + tabel `enrich_queue`
- `ipintel/db.py` + `schema.sql` — skema Postgres
- `ipintel/config.py` — kredensial (bisa dioverride env `PG_*`, `ABUSE_KEY`, `VT_KEY`)
- `ipintel/docs/` — STRUCTURE.md, graph.html, graph.json (graphify)
- CSV: `unsaved (3).csv` (asli), `*-no-cloudflare.csv`, `*-abused.csv`, `*-cloudflare-only.csv`, `cloudflare-ranges.csv`, `ipv6-backup.csv`
