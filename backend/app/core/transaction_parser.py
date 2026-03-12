from typing import List, Dict, Any, Optional
from decimal import Decimal
from dataclasses import dataclass
from enum import Enum


class FlowDirection(str, Enum):
    INFLOW = "inflow"
    OUTFLOW = "outflow"


@dataclass
class TokenTransfer:
    """Representa una transferencia de tokens SPL."""
    mint: str
    token_symbol: Optional[str]
    amount: Decimal
    decimals: int
    source: str
    destination: str
    direction: FlowDirection  # Relativo al wallet principal


@dataclass
class SOLTransfer:
    """Representa una transferencia de SOL (en lamports)."""
    amount_lamports: int
    source: str
    destination: str
    direction: FlowDirection


@dataclass
class ParsedTransaction:
    """Transacción parseada con todos los flujos extraídos."""
    signature: str
    slot: int
    block_time: int
    success: bool
    fee: int
    sol_transfers: List[SOLTransfer]
    token_transfers: List[TokenTransfer]
    program_ids: List[str]
    raw_data: Dict[str, Any]


class TransactionParser:
    """
    Parser de transacciones de Solana.
    Extrae transfers de SOL y tokens SPL de los datos de Helius.
    """

    def __init__(self, target_address: str):
        self.target_address = target_address

    def parse_transaction(self, tx_data: Dict[str, Any]) -> ParsedTransaction:
        """Parsea una transacción completa de Helius."""
        transaction = tx_data.get("transaction", {})
        meta = tx_data.get("meta", {})

        signature = transaction.get("signatures", [""])[0]
        slot = tx_data.get("slot", 0)
        block_time = tx_data.get("blockTime", 0)
        success = meta.get("err") is None
        fee = meta.get("fee", 0)

        message = transaction.get("message", {})
        account_keys = self._extract_account_keys(message)

        sol_transfers = self._parse_sol_transfers(meta, account_keys)
        token_transfers = self._parse_token_transfers(meta, account_keys)
        program_ids = self._extract_program_ids(message)

        return ParsedTransaction(
            signature=signature,
            slot=slot,
            block_time=block_time,
            success=success,
            fee=fee,
            sol_transfers=sol_transfers,
            token_transfers=token_transfers,
            program_ids=program_ids,
            raw_data=tx_data,
        )

    def _extract_account_keys(self, message: Dict[str, Any]) -> List[str]:
        """Extrae todas las account keys del mensaje (soporte v0)."""
        account_keys = []
        for key in message.get("accountKeys", []):
            if isinstance(key, str):
                account_keys.append(key)
            elif isinstance(key, dict):
                account_keys.append(key.get("pubkey", ""))
        return account_keys

    def _parse_sol_transfers(
        self, meta: Dict[str, Any], account_keys: List[str]
    ) -> List[SOLTransfer]:
        """Extrae transfers de SOL comparando pre/post balances."""
        transfers = []
        pre_balances = meta.get("preBalances", [])
        post_balances = meta.get("postBalances", [])

        if len(pre_balances) != len(post_balances):
            return transfers

        # Mapa de cambios netos de balance por dirección
        senders: List[str] = []
        receivers: List[str] = []

        for i, (pre, post) in enumerate(zip(pre_balances, post_balances)):
            if i >= len(account_keys):
                continue
            change = post - pre
            if change > 0:
                receivers.append(account_keys[i])
            elif change < 0:
                senders.append(account_keys[i])

        for receiver in receivers:
            for sender in senders:
                direction = (
                    FlowDirection.INFLOW
                    if receiver == self.target_address
                    else FlowDirection.OUTFLOW
                )
                transfers.append(
                    SOLTransfer(
                        amount_lamports=1,  # Placeholder; real amount from balance diffs
                        source=sender,
                        destination=receiver,
                        direction=direction,
                    )
                )

        # Simplified: one SOL transfer entry per sender→receiver pair with correct amount
        # Re-compute with actual amounts
        transfers = []
        balance_changes = {}
        for i, (pre, post) in enumerate(zip(pre_balances, post_balances)):
            if i < len(account_keys):
                change = post - pre
                if change != 0:
                    balance_changes[account_keys[i]] = change

        for address, change in balance_changes.items():
            if change > 0 and address != self.target_address:
                # Someone else received: could be outflow target
                direction = FlowDirection.OUTFLOW
                transfers.append(
                    SOLTransfer(
                        amount_lamports=change,
                        source=self.target_address,
                        destination=address,
                        direction=direction,
                    )
                )
            elif change > 0 and address == self.target_address:
                direction = FlowDirection.INFLOW
                transfers.append(
                    SOLTransfer(
                        amount_lamports=change,
                        source="unknown",
                        destination=address,
                        direction=direction,
                    )
                )
            elif change < 0 and address == self.target_address:
                direction = FlowDirection.OUTFLOW
                transfers.append(
                    SOLTransfer(
                        amount_lamports=abs(change),
                        source=address,
                        destination="unknown",
                        direction=direction,
                    )
                )

        return transfers

    def _parse_token_transfers(
        self, meta: Dict[str, Any], account_keys: List[str]
    ) -> List[TokenTransfer]:
        """Extrae transfers de tokens SPL de pre/postTokenBalances."""
        transfers = []
        pre_token_balances = meta.get("preTokenBalances", [])
        post_token_balances = meta.get("postTokenBalances", [])

        # Mapa (accountIndex, mint) → balance
        pre_map: Dict = {}
        for balance in pre_token_balances:
            key = (balance.get("accountIndex"), balance.get("mint"))
            amount = balance.get("uiTokenAmount", {}).get("amount", "0")
            pre_map[key] = {
                "amount": int(amount),
                "decimals": balance.get("uiTokenAmount", {}).get("decimals", 0),
                "owner": balance.get("owner", ""),
            }

        post_map: Dict = {}
        for balance in post_token_balances:
            key = (balance.get("accountIndex"), balance.get("mint"))
            amount = balance.get("uiTokenAmount", {}).get("amount", "0")
            post_map[key] = {
                "amount": int(amount),
                "decimals": balance.get("uiTokenAmount", {}).get("decimals", 0),
                "owner": balance.get("owner", ""),
            }

        all_keys = set(pre_map.keys()) | set(post_map.keys())

        for key in all_keys:
            account_index, mint = key
            if not mint:
                continue

            pre_data = pre_map.get(key, {"amount": 0, "decimals": 0, "owner": ""})
            post_data = post_map.get(key, {"amount": 0, "decimals": 0, "owner": ""})

            change = post_data["amount"] - pre_data["amount"]
            if change == 0:
                continue

            owner = post_data["owner"] or pre_data["owner"]
            decimals = post_data["decimals"] or pre_data["decimals"]
            decimals = max(decimals, 0)

            if change > 0:
                direction = (
                    FlowDirection.INFLOW
                    if owner == self.target_address
                    else FlowDirection.OUTFLOW
                )
                transfers.append(
                    TokenTransfer(
                        mint=mint,
                        token_symbol=None,
                        amount=Decimal(change) / Decimal(10**decimals) if decimals > 0 else Decimal(change),
                        decimals=decimals,
                        source="unknown",
                        destination=owner,
                        direction=direction,
                    )
                )
            else:
                direction = (
                    FlowDirection.OUTFLOW
                    if owner == self.target_address
                    else FlowDirection.INFLOW
                )
                transfers.append(
                    TokenTransfer(
                        mint=mint,
                        token_symbol=None,
                        amount=Decimal(abs(change)) / Decimal(10**decimals) if decimals > 0 else Decimal(abs(change)),
                        decimals=decimals,
                        source=owner,
                        destination="unknown",
                        direction=direction,
                    )
                )

        return transfers

    def _extract_program_ids(self, message: Dict[str, Any]) -> List[str]:
        """Extrae program IDs de las instrucciones."""
        program_ids = set()
        for instruction in message.get("instructions", []):
            if isinstance(instruction, dict):
                program_id = instruction.get("programId")
                if program_id:
                    program_ids.add(program_id)
        return list(program_ids)
