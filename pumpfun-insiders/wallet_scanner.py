"""Scan a supplied launch manifest; emit recurrence and coverage, never verdicts."""
import argparse
import json
from core import RPC, PUMP, save, trades


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", default="data/launches.json")
    p.add_argument("--config", default="config.example.json")
    p.add_argument("--out", default="data/scan.json")
    args = p.parse_args()
    config = json.load(open(args.config))
    launches = json.load(open(args.manifest))
    if not launches:
        p.error("Manifest is empty. Add verified launch records first.")
    if len({x["mint"] for x in launches}) != len(launches):
        p.error("Duplicate launch mint")
    rpc = RPC(config["cache_dir"])
    rows, coverage = [], []
    for launch in launches:
        creation = rpc.tx(launch["creation_signature"])
        if not creation or creation.get("meta", {}).get("err") is not None:
            raise ValueError("Creation transaction missing or unsuccessful")
        start = creation["slot"]
        end = start + config["early_slot_window"]
        signatures, complete = rpc.history(launch["bonding_curve"], start, config["max_pages"])
        missing, unsupported, candidate_count = [], [], 0
        launch_rows = []
        for item in signatures:
            if item["slot"] > end or item.get("err") is not None:
                continue
            candidate_count += 1
            tx = rpc.tx(item["signature"])
            if not tx:
                missing.append(item["signature"])
                continue
            events = trades(tx, config.get("program_id", PUMP))
            matching = [e for e in events if e["mint"] == launch["mint"]]
            if not matching:
                unsupported.append(item["signature"])
            for event in matching:
                if not event["is_buy"]:
                    continue
                purchase_time, creation_time = tx.get("blockTime"), creation.get("blockTime")
                launch_rows.append({**event, "purchase_signature": item["signature"],
                    "creation_signature": launch["creation_signature"],
                    "creation_slot": start, "slot": tx["slot"],
                    "block_time": purchase_time,
                    "time_offset_seconds": purchase_time - creation_time
                        if purchase_time is not None and creation_time is not None else None,
                    "same_creation_transaction": item["signature"] == launch["creation_signature"],
                    "quote_asset": "SOL", "decoder": "legacy_trade_event_prefix_v1"})
        # Slot ordering only: no invented ordering of transactions within a slot.
        launch_rows.sort(key=lambda x: (x["slot"], x["purchase_signature"], x["log_index"]))
        rows.extend(launch_rows)
        coverage.append({"mint": launch["mint"], "history_boundary_reached": complete,
            "candidate_transactions": candidate_count, "missing_transactions": missing,
            "transactions_without_matching_event": unsupported,
            "creation_verified_as_launch": False,
            "note": "Manifest roles are user supplied; no unique-buyer rank inferred."})
    wallets = {}
    for row in rows:
        wallets.setdefault(row["wallet"], set()).add(row["mint"])
    save(args.out, {"schema_version": "1.0", "scope": "manifest_only",
        "quote_scope": "legacy_SOL_events_only", "purchases": rows, "coverage": coverage,
        "recurrence": [{"wallet": w, "launch_count": len(m), "mints": sorted(m)}
                       for w, m in sorted(wallets.items(), key=lambda x: (-len(x[1]), x[0]))]})
    print("Saved", args.out, "with", len(rows), "decoded purchases")


if __name__ == "__main__":
    main()
