import httpx
import asyncio
from typing import Optional, List, Dict, Any
from ..config import settings


class HeliusClient:
    """
    Cliente para interactuar con la API de Helius.
    Usa getTransactionsForAddress para trazabilidad completa.
    """

    def __init__(self):
        self.base_url = f"{settings.HELIUS_RPC_URL}/?api-key={settings.HELIUS_API_KEY}"
        print(f"🚀 HeliusClient using URL: {self.base_url[:45]}...")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_transactions_for_address(
        self,
        address: str,
        transaction_details: str = "full",
        sort_order: str = "desc",
        limit: int = 100,
        pagination_token: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Obtiene transacciones para una dirección usando getTransactionsForAddress.

        Filtros disponibles:
        - blockTime: {"gte": timestamp, "lte": timestamp}
        - status: "succeeded" | "failed" | "any"
        - tokenAccounts: "none" | "balanceChanged" | "all"
        - slot: {"gte": slot, "lte": slot}
        """
        params: Dict[str, Any] = {
            "transactionDetails": transaction_details,
            "sortOrder": sort_order,
            "limit": min(limit, 100 if transaction_details == "full" else 1000),
            "encoding": "jsonParsed",
            "maxSupportedTransactionVersion": 0,
        }

        if pagination_token:
            params["paginationToken"] = pagination_token

        if filters:
            params["filters"] = filters

        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getTransactionsForAddress",
            "params": [address, params],
        }

        response = await self.client.post(self.base_url, json=payload)
        
        # Fallback to standard RPC if Enhanced API is forbidden (Free Tier)
        if response.status_code in (403, 401) or "paid plans" in response.text:
            print(f"⚠️ Helius Enhanced API forbidden (Free Tier). Falling back to standard RPC for {address}...")
            return await self._get_transactions_standard_rpc(address, limit, pagination_token)
            
        response.raise_for_status()
        return response.json()

    async def _get_transactions_standard_rpc(self, address: str, limit: int, before: Optional[str] = None) -> Dict[str, Any]:
        """
        Fallback method using standard Solana RPC:
        1. getSignaturesForAddress
        2. batch getTransaction (jsonParsed)
        """
        # 1. Get signatures
        sig_params = {"limit": limit}
        if before:
            sig_params["before"] = before
            
        sig_payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getSignaturesForAddress",
            "params": [address, sig_params],
        }
        sig_resp = await self.client.post(self.base_url, json=sig_payload)
        sig_resp.raise_for_status()
        signatures_data = sig_resp.json().get("result", [])
        
        if not signatures_data:
            return {"result": {"data": [], "paginationToken": None}}
            
        signatures = [s["signature"] for s in signatures_data]
        last_signature = signatures[-1] if len(signatures) == limit else None
        
        # 2. Concurrent getTransaction requests
        async def fetch_tx(sig):
            payload = {
                "jsonrpc": "2.0",
                "id": sig,
                "method": "getTransaction",
                "params": [sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
            }
            try:
                resp = await self.client.post(self.base_url, json=payload)
                resp.raise_for_status()
                return resp.json().get("result")
            except Exception as e:
                print(f"Error fetching tx {sig}: {e}")
                return None
                
        sem = asyncio.Semaphore(5) # Conservative concurrency for Free Tier
        async def fetch_with_sem(sig):
            async with sem:
                return await fetch_tx(sig)
                
        tasks = [fetch_with_sem(sig) for sig in signatures]
        results = await asyncio.gather(*tasks)
        
        parsed_transactions = [res for res in results if res is not None]
                    
        return {"result": {"data": parsed_transactions, "paginationToken": last_signature}}

    async def get_all_transactions(
        self,
        address: str,
        filters: Optional[Dict[str, Any]] = None,
        max_transactions: int = 1000,
    ) -> List[Dict[str, Any]]:
        """
        Pagina a través de todas las transacciones hasta el límite máximo.
        """
        all_transactions: List[Dict[str, Any]] = []
        pagination_token: Optional[str] = None

        while len(all_transactions) < max_transactions:
            result = await self.get_transactions_for_address(
                address=address,
                transaction_details="full",
                pagination_token=pagination_token,
                filters=filters,
            )

            data = result.get("result", {})
            if isinstance(data, dict):
                transactions = data.get("data", [])
                pagination_token = data.get("paginationToken")
            else:
                # Older format: result is directly a list
                transactions = data if isinstance(data, list) else []
                pagination_token = None

            if not transactions:
                break

            all_transactions.extend(transactions)

            if not pagination_token:
                break

            await asyncio.sleep(0.1)  # Rate limiting

        return all_transactions[:max_transactions]

    async def get_token_metadata(self, mint_address: str) -> Dict[str, Any]:
        """
        Obtiene metadata de un token usando DAS API (getAsset).
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "getAsset",
            "params": {"id": mint_address},
        }

        response = await self.client.post(self.base_url, json=payload)
        response.raise_for_status()
        return response.json()

    async def close(self):
        await self.client.aclose()
