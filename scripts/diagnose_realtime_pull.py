"""Read-only diagnostic for the Realtime "Pull sekarang" flow.

Answers the common question: "I pulled the last 24 hours but only got 1 new
alert, while the index seems to hold thousands." It compares:

* the configured severity range and max_alerts,
* how many documents the Wazuh Indexer returns for the all-time and 24h
  windows using the exact same query the pull uses,
* how many of those documents already exist in the Arbiter database.

Nothing is written to Wazuh or to the Arbiter database.

Usage inside the Arbiter container (from the project root):

    sudo docker compose exec arbiter python -m scripts.diagnose_realtime_pull
    sudo docker compose exec arbiter python -m scripts.diagnose_realtime_pull --hours 24 --limit 5000
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone

from app.database import get_db
from app.settings import load_settings, wazuh_password, wazuh_search


def _fmt(value: object) -> str:
    return "-" if value is None or value == "" else str(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diagnose Realtime pull counts (read-only).")
    parser.add_argument(
        "--hours",
        type=float,
        default=24.0,
        help="Window in hours to compare against all-time (default: 24).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5000,
        help="Maximum documents to sample per window (default: 5000).",
    )
    args = parser.parse_args(argv)

    with get_db() as conn:
        stored = load_settings(conn)
        db_total = conn.execute("SELECT count(*) FROM wazuh.alerts").fetchone()[0]
        db_levels = conn.execute(
            """
            SELECT rule_level, count(*) AS n
            FROM wazuh.alerts
            GROUP BY rule_level
            ORDER BY rule_level
            """
        ).fetchall()

    wazuh = stored.get("wazuh", {})
    realtime = stored.get("realtime", {})
    if not wazuh.get("indexer_url"):
        print("Wazuh Indexer belum dikonfigurasi di Arbiter.", file=sys.stderr)
        return 2

    min_level = int(realtime.get("min_rule_level") if realtime.get("min_rule_level") is not None else 7)
    raw_max = realtime.get("max_rule_level")
    max_level = int(raw_max) if raw_max is not None and str(raw_max).strip() != "" else None
    configured_max = int(realtime.get("max_alerts") or 500)
    limit = max(1, min(args.limit, configured_max, 100000))

    since_dt = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    since = since_dt.isoformat()

    base_kwargs = dict(
        indexer_url=wazuh.get("indexer_url", ""),
        username=wazuh.get("username", ""),
        password=wazuh_password(stored),
        index_pattern=wazuh.get("index_pattern", "wazuh-alerts-*"),
        verify_tls=bool(wazuh.get("verify_tls", True)),
        min_rule_level=min_level,
        max_rule_level=max_level,
    )

    print("=== Konfigurasi ===")
    print(f"index_pattern : {_fmt(wazuh.get('index_pattern'))}")
    print(f"severity      : min={min_level} max={_fmt(max_level)}")
    print(f"max_alerts    : {configured_max} (sample limit={limit})")
    print(f"mode          : {_fmt(realtime.get('mode'))}")
    print(f"last_pull_at  : {_fmt(realtime.get('last_pull_at'))}")
    print()

    all_time = wazuh_search(**base_kwargs, size=limit)
    last_window = wazuh_search(**base_kwargs, size=limit, since=since)

    print("=== Wazuh (query yang sama dengan pull) ===")
    print(f"semua waktu   : {len(all_time)} dokumen (maks {limit})")
    print(f"{args.hours:g} jam terakhir: {len(last_window)} dokumen (sejak {since})")
    if len(all_time) >= limit:
        print(f"CATATAN: hasil 'semua waktu' mentok di batas {limit}; sebenarnya bisa lebih banyak.")
    if len(last_window) >= limit:
        print(f"CATATAN: hasil {args.hours:g} jam mentok di batas {limit}; sebenarnya bisa lebih banyak.")
    print()

    def _ids(docs: list[dict]) -> list[str]:
        return [str(d.get("id") or d.get("_id") or "") for d in docs if d.get("id") or d.get("_id")]

    def _existing(ids: list[str]) -> int:
        ids = [i for i in ids if i]
        if not ids:
            return 0
        with get_db() as conn:
            row = conn.execute(
                "SELECT count(*) FROM wazuh.alerts WHERE alert_id = ANY(%s)",
                (ids,),
            ).fetchone()
        return int(row[0] if row else 0)

    all_ids = _ids(all_time)
    win_ids = _ids(last_window)
    all_existing = _existing(all_ids)
    win_existing = _existing(win_ids)

    print("=== Arbiter DB ===")
    print(f"total alert di DB : {db_total}")
    for row in db_levels:
        print(f"  rule.level {_fmt(row[0])}: {row[1]}")
    print()
    print("=== Dedup terhadap DB ===")
    print(f"semua waktu   : {all_existing}/{len(all_ids)} sudah ada di DB, {len(all_ids) - all_existing} baru")
    print(f"{args.hours:g} jam terakhir: {win_existing}/{len(win_ids)} sudah ada di DB, {len(win_ids) - win_existing} baru")
    print()
    print(
        "Kesimpulan: jika 'baru' kecil padahal dokumen banyak, alert tersebut memang "
        "sudah pernah masuk (dedup), bukan karena filter waktu atau tombol pull gagal."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
