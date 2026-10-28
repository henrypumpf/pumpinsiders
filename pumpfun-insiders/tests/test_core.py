import base64
import struct
import unittest
from unittest.mock import patch
from core import PUMP, TRADE, RPC, b58, trades, native_transfers


def fixture(raw, program=PUMP):
    return {"meta": {"err": None, "logMessages": [
        f"Program {program} invoke [1]",
        "Program data: " + base64.b64encode(raw).decode(),
        f"Program {program} success"]}}


class DecoderTests(unittest.TestCase):
    def event(self):
        return TRADE + bytes([1]) * 32 + struct.pack("<QQB", 500, 100, 1) + bytes([2]) * 32 + struct.pack("<qQQQQ", 1700000000, 1, 2, 3, 4)

    def test_trade(self):
        event = trades(fixture(self.event()))[0]
        self.assertEqual(event["quote_amount_raw"], 500)
        self.assertEqual(event["wallet"], b58(bytes([2]) * 32))
        self.assertTrue(event["is_buy"])

    def test_failed_transaction(self):
        tx = fixture(self.event())
        tx["meta"]["err"] = {"InstructionError": [0, "failure"]}
        self.assertEqual(trades(tx), [])

    def test_foreign_program_and_extended_layout(self):
        self.assertEqual(trades(fixture(self.event(), "other")), [])
        self.assertEqual(trades(fixture(self.event() + b"extension")), [])
        self.assertEqual(trades(fixture(self.event()[:50])), [])

    def test_nested_program_not_attributed(self):
        tx = fixture(self.event(), "other")
        tx["meta"]["logMessages"].insert(0, f"Program {PUMP} invoke [1]")
        self.assertEqual(trades(tx), [])

    def test_native_transfer(self):
        ins = {"programId": "11111111111111111111111111111111", "parsed": {
            "type": "transfer", "info": {"source": "A", "destination": "B", "lamports": 42}}}
        tx = {"meta": {"err": None, "innerInstructions": [{"index": 1, "instructions": [ins]}]},
              "transaction": {"message": {"instructions": []}}}
        self.assertEqual(native_transfers(tx)[0]["lamports"], 42)
        self.assertEqual(native_transfers(tx)[0]["instruction_path"], "inner:1:0")
        ins["programId"] = "other"
        self.assertEqual(native_transfers(tx), [])

    def test_history_limit_is_incomplete(self):
        with patch.dict("os.environ", {"SOLANA_RPC_URL": "https://example.invalid"}):
            rpc = RPC("unused")
        rpc.call = lambda *args: [{"signature": str(i), "slot": 100} for i in range(1000)]
        rows, complete = rpc.history("address", 90, 1)
        self.assertFalse(complete)
        self.assertEqual(len(rows), 1000)

    def test_history_boundary(self):
        with patch.dict("os.environ", {"SOLANA_RPC_URL": "https://example.invalid"}):
            rpc = RPC("unused")
        rpc.call = lambda *args: [{"signature": "one", "slot": 100}, {"signature": "two", "slot": 80}]
        rows, complete = rpc.history("address", 90, 1)
        self.assertTrue(complete)
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
