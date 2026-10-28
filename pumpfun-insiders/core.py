"""Standard-library RPC and deliberately narrow, auditable event decoding."""
import base64
import hashlib
import json
import os
import struct
import time
import urllib.error
import urllib.request
from pathlib import Path

PUMP = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"
ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
TRADE = hashlib.sha256(b"event:TradeEvent").digest()[:8]


def b58(raw):
    n = int.from_bytes(raw, "big")
    result = ""
    while n:
        n, rem = divmod(n, 58)
        result = ALPHABET[rem] + result
    return "1" * (len(raw) - len(raw.lstrip(b"\0"))) + result


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, indent=2) + "\n")
    temp.replace(path)


class RPC:
    def __init__(self, cache):
        self.url = os.environ.get("SOLANA_RPC_URL")
        if not self.url:
            raise ValueError("Set SOLANA_RPC_URL to a Solana mainnet RPC endpoint")
        self.cache = Path(cache)

    def call(self, method, params):
        payload = json.dumps({"jsonrpc": "2.0", "id": 1,
                              "method": method, "params": params}).encode()
        key = hashlib.sha256(payload).hexdigest()
        path = self.cache / (key + ".json")
        if path.exists():
            return json.loads(path.read_text())["result"]
        for attempt in range(5):
            request = urllib.request.Request(self.url, data=payload,
                                            headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(request, timeout=45) as response:
                    body = json.load(response)
                if "error" in body:
                    raise RuntimeError("RPC returned error code " + str(body["error"].get("code")))
                if body.get("result") is not None:
                    save(path, body)
                return body.get("result")
            except (urllib.error.URLError, TimeoutError, RuntimeError):
                if attempt == 4:
                    raise RuntimeError("RPC request failed: " + method) from None
                time.sleep(min(2 ** attempt, 8))

    def tx(self, signature):
        return self.call("getTransaction", [signature, {
            "encoding": "jsonParsed", "commitment": "finalized",
            "maxSupportedTransactionVersion": 0}])

    def history(self, address, min_slot, max_pages):
        rows, before = [], None
        for _ in range(max_pages):
            config = {"limit": 1000, "commitment": "finalized"}
            if before:
                config["before"] = before
            page = self.call("getSignaturesForAddress", [address, config])
            if not page:
                return rows, True
            rows.extend(x for x in page if x["slot"] >= min_slot)
            if page[-1]["slot"] < min_slot or len(page) < 1000:
                return rows, True
            if page[-1]["signature"] == before:
                raise RuntimeError("Pagination did not advance")
            before = page[-1]["signature"]
        return rows, False


def trades(tx, program=PUMP):
    """Decode the documented legacy TradeEvent prefix; ignore unknown events.

    Only logs emitted within the target program's active invocation are accepted.
    Only the original 129-byte SOL event is supported. Extended layouts are rejected.
    """
    if not tx or not tx.get("meta") or tx["meta"].get("err") is not None:
        return []
    stack, result = [], []
    for log in tx["meta"].get("logMessages") or []:
        if log.startswith("Program ") and " invoke [" in log:
            stack.append(log.split()[1])
        elif log.startswith("Program ") and (log.endswith(" success") or " failed:" in log):
            if stack and stack[-1] == log.split()[1]:
                stack.pop()
        elif log.startswith("Program data: ") and stack and stack[-1] == program:
            try:
                raw = base64.b64decode(log[14:], validate=True)
            except ValueError:
                continue
            if len(raw) != 129 or raw[:8] != TRADE or raw[56] not in (0, 1):
                continue
            result.append({"mint": b58(raw[8:40]),
                           "quote_amount_raw": struct.unpack_from("<Q", raw, 40)[0],
                           "token_amount_raw": struct.unpack_from("<Q", raw, 48)[0],
                           "is_buy": bool(raw[56]), "wallet": b58(raw[57:89]),
                           "event_timestamp": struct.unpack_from("<q", raw, 89)[0],
                           "event_bytes": len(raw), "log_index": len(result)})
    return result


def native_transfers(tx):
    """Explicit parsed System Program transfers only; no balance-delta inference."""
    if not tx or not tx.get("meta") or tx["meta"].get("err") is not None:
        return []
    groups = [("outer", tx["transaction"]["message"]["instructions"])]
    groups += [("inner:" + str(g["index"]), g["instructions"])
               for g in tx["meta"].get("innerInstructions") or []]
    result = []
    for location, instructions in groups:
        for index, ins in enumerate(instructions):
            parsed = ins.get("parsed", {})
            if ins.get("programId") != "11111111111111111111111111111111":
                continue
            if parsed.get("type") not in ("transfer", "transferWithSeed"):
                continue
            info = parsed["info"]
            result.append({"source": info["source"], "destination": info["destination"],
                           "lamports": int(info["lamports"]),
                           "instruction_path": location + ":" + str(index)})
    return result
