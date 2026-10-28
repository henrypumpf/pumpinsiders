"""Find observed shared direct SOL senders before early buys; no ownership inference."""
import argparse
import json
from collections import defaultdict
from core import RPC, native_transfers, save


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scan", default="data/scan.json")
    p.add_argument("--config", default="config.example.json")
    p.add_argument("--out", default="wallet_clusters.json")
    args = p.parse_args()
    config = json.load(open(args.config))
    purchases = json.load(open(args.scan))["purchases"]
    rpc = RPC(config["cache_dir"])
    edges, coverage = [], []
    by_wallet = defaultdict(list)
    for buy in purchases:
        by_wallet[buy["wallet"]].append(buy)
    for wallet, buys in sorted(by_wallet.items()):
        # Slot floor is explicit and independent of unreliable seconds-to-slot estimates.
        floor = max(0, min(b["slot"] for b in buys) - config["funding_lookback_slots"])
        signatures, complete = rpc.history(wallet, floor, config["max_pages"])
        missing, unknown_time = [], []
        for item in signatures:
            if item.get("err") is not None:
                continue
            if item["slot"] >= max(b["slot"] for b in buys):
                continue
            tx = rpc.tx(item["signature"])
            if not tx:
                missing.append(item["signature"])
                continue
            if tx.get("blockTime") is None:
                unknown_time.append(item["signature"])
                continue
            eligible = [b for b in buys if b["slot"] > tx["slot"]
                and b["block_time"] is not None
                and 0 <= b["block_time"] - tx["blockTime"] <= config["funding_lookback_seconds"]]
            if not eligible:
                continue
            for transfer in native_transfers(tx):
                if transfer["destination"] != wallet or transfer["source"] == wallet:
                    continue
                if transfer["lamports"] < config["min_funding_lamports"]:
                    continue
                edges.append({**transfer, "signature": item["signature"], "slot": tx["slot"],
                    "block_time": tx["blockTime"], "source_classification": "unresolved",
                    "related_purchase_signatures": sorted({b["purchase_signature"] for b in eligible})})
        coverage.append({"wallet": wallet, "history_boundary_reached": complete,
            "minimum_slot": floor, "missing_transactions": missing,
            "transactions_with_unknown_time": unknown_time,
            "buys_with_unknown_time": sum(b["block_time"] is None for b in buys)})
    sources = defaultdict(set)
    for e in edges:
        sources[e["source"]].add(e["destination"])
    candidates = [{"candidate_id": "source-" + source,
        "shared_source": source, "members": sorted(members),
        "relationship": "observed_shared_direct_sender",
        "source_classification": "unresolved", "common_control_established": False,
        "evidence": [e for e in edges if e["source"] == source],
        "alternative_explanations": ["public_service", "custodian", "independent_recipients"]}
        for source, members in sorted(sources.items()) if len(members) >= 2]
    save(args.out, {"schema_version": "1.0", "status": "observational_candidates",
        "clusters": candidates, "funding_edges": edges, "coverage": coverage,
        "limitations": ["SOL parsed System Program transfers only", "One hop only",
            "Same-slot funding excluded because transaction order is unresolved",
            "No attribution of exact spent funds", "Public services not automatically classified"]})
    print("Saved", args.out, "with", len(candidates), "shared-source candidates")


if __name__ == "__main__":
    main()
