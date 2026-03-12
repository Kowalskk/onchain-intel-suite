import asyncio
import json
from app.core.helius_client import HeliusClient
from app.core.transaction_parser import TransactionParser

async def test():
    client = HeliusClient()
    addr = "vines1vzrYbzLMRdu58ou5XTby4qAqVRLmqo36NKPTg"
    print("Fetching txs...")
    res = await client._get_transactions_standard_rpc(addr, 2)
    txs = res["result"]["data"]
    print(f"Got {len(txs)} txs.")
    if txs:
        parser = TransactionParser(addr)
        parsed = parser.parse_transaction(txs[0])
        print("Success:", parsed.success)
        print("SOL transfers:", len(parsed.sol_transfers))
        print("Token transfers:", len(parsed.token_transfers))
        print("Signatures:", parsed.signature)
        # Optionally show raw if 0
        if len(parsed.sol_transfers) == 0 and len(parsed.token_transfers) == 0:
            print(json.dumps(txs[0]["transaction"]["message"]["accountKeys"][:2], indent=2))
            
if __name__ == "__main__":
    asyncio.run(test())
