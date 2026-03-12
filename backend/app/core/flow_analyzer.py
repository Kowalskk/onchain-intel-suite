from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from decimal import Decimal
from collections import defaultdict

from .transaction_parser import ParsedTransaction, FlowDirection, TokenTransfer, SOLTransfer


@dataclass
class CounterpartyStats:
    """Estadísticas agregadas de una contraparte."""
    address: str
    label: Optional[str] = None  # "Binance", "Raydium", etc.
    total_transactions: int = 0
    total_inflow_sol: Decimal = field(default_factory=Decimal)
    total_outflow_sol: Decimal = field(default_factory=Decimal)
    total_inflow_tokens: Dict[str, Decimal] = field(default_factory=dict)
    total_outflow_tokens: Dict[str, Decimal] = field(default_factory=dict)
    first_interaction: Optional[int] = None
    last_interaction: Optional[int] = None
    transaction_signatures: List[str] = field(default_factory=list)


@dataclass
class WalletFlowSummary:
    """Resumen completo de flujos de una wallet."""
    address: str
    total_transactions: int
    total_counterparties: int
    date_range: tuple  # (first_tx_timestamp, last_tx_timestamp)

    # SOL totals
    total_sol_inflow: Decimal
    total_sol_outflow: Decimal

    # Token totals por mint
    token_inflows: Dict[str, Decimal]
    token_outflows: Dict[str, Decimal]

    # Tokens únicos vistos
    unique_tokens: Set[str]

    # Top counterparties
    top_inflow_counterparties: List[CounterpartyStats]
    top_outflow_counterparties: List[CounterpartyStats]


class FlowAnalyzer:
    """
    Analiza flujos de fondos para una wallet.
    Agrega estadísticas por contraparte y token.
    """

    def __init__(self, target_address: str):
        self.target_address = target_address
        self.counterparties: Dict[str, CounterpartyStats] = {}
        self.parsed_transactions: List[ParsedTransaction] = []

    def add_transaction(self, parsed_tx: ParsedTransaction):
        """Procesa una transacción parseada y agrega sus flujos."""
        self.parsed_transactions.append(parsed_tx)

        for sol_transfer in parsed_tx.sol_transfers:
            self._process_sol_transfer(sol_transfer, parsed_tx)

        for token_transfer in parsed_tx.token_transfers:
            self._process_token_transfer(token_transfer, parsed_tx)

    def _process_sol_transfer(self, transfer: SOLTransfer, tx: ParsedTransaction):
        if transfer.direction == FlowDirection.INFLOW:
            counterparty = transfer.source
        else:
            counterparty = transfer.destination

        if counterparty in ("unknown", "aggregated", self.target_address, ""):
            return

        stats = self._get_or_create_counterparty(counterparty)
        amount_sol = Decimal(transfer.amount_lamports) / Decimal(1_000_000_000)

        if transfer.direction == FlowDirection.INFLOW:
            stats.total_inflow_sol += amount_sol
        else:
            stats.total_outflow_sol += amount_sol

        self._update_counterparty_stats(stats, tx)

    def _process_token_transfer(self, transfer: TokenTransfer, tx: ParsedTransaction):
        if transfer.direction == FlowDirection.INFLOW:
            counterparty = transfer.source
        else:
            counterparty = transfer.destination

        if counterparty in ("unknown", "aggregated", self.target_address, ""):
            return

        stats = self._get_or_create_counterparty(counterparty)

        if transfer.direction == FlowDirection.INFLOW:
            if transfer.mint not in stats.total_inflow_tokens:
                stats.total_inflow_tokens[transfer.mint] = Decimal(0)
            stats.total_inflow_tokens[transfer.mint] += transfer.amount
        else:
            if transfer.mint not in stats.total_outflow_tokens:
                stats.total_outflow_tokens[transfer.mint] = Decimal(0)
            stats.total_outflow_tokens[transfer.mint] += transfer.amount

        self._update_counterparty_stats(stats, tx)

    def _get_or_create_counterparty(self, address: str) -> CounterpartyStats:
        if address not in self.counterparties:
            self.counterparties[address] = CounterpartyStats(address=address)
        return self.counterparties[address]

    def _update_counterparty_stats(self, stats: CounterpartyStats, tx: ParsedTransaction):
        stats.total_transactions += 1
        if tx.signature not in stats.transaction_signatures:
            stats.transaction_signatures.append(tx.signature)

        if stats.first_interaction is None or tx.block_time < stats.first_interaction:
            stats.first_interaction = tx.block_time
        if stats.last_interaction is None or tx.block_time > stats.last_interaction:
            stats.last_interaction = tx.block_time

    def get_summary(self) -> WalletFlowSummary:
        """Genera resumen completo de flujos."""
        total_sol_inflow = Decimal(0)
        total_sol_outflow = Decimal(0)
        token_inflows: Dict[str, Decimal] = defaultdict(Decimal)
        token_outflows: Dict[str, Decimal] = defaultdict(Decimal)
        unique_tokens: Set[str] = set()

        for stats in self.counterparties.values():
            total_sol_inflow += stats.total_inflow_sol
            total_sol_outflow += stats.total_outflow_sol

            for mint, amount in stats.total_inflow_tokens.items():
                token_inflows[mint] += amount
                unique_tokens.add(mint)

            for mint, amount in stats.total_outflow_tokens.items():
                token_outflows[mint] += amount
                unique_tokens.add(mint)

        # Ordenar por volumen
        sorted_by_inflow = sorted(
            self.counterparties.values(),
            key=lambda x: x.total_inflow_sol + sum(x.total_inflow_tokens.values()),
            reverse=True,
        )[:20]

        sorted_by_outflow = sorted(
            self.counterparties.values(),
            key=lambda x: x.total_outflow_sol + sum(x.total_outflow_tokens.values()),
            reverse=True,
        )[:20]

        timestamps = [tx.block_time for tx in self.parsed_transactions if tx.block_time]
        date_range = (min(timestamps), max(timestamps)) if timestamps else (0, 0)

        return WalletFlowSummary(
            address=self.target_address,
            total_transactions=len(self.parsed_transactions),
            total_counterparties=len(self.counterparties),
            date_range=date_range,
            total_sol_inflow=total_sol_inflow,
            total_sol_outflow=total_sol_outflow,
            token_inflows=dict(token_inflows),
            token_outflows=dict(token_outflows),
            unique_tokens=unique_tokens,
            top_inflow_counterparties=sorted_by_inflow,
            top_outflow_counterparties=sorted_by_outflow,
        )

    def get_flows_for_token(self, mint: str) -> List[Dict[str, Any]]:
        """Obtiene todos los flujos para un token específico."""
        flows = []
        for stats in self.counterparties.values():
            if mint in stats.total_inflow_tokens:
                flows.append({
                    "address": stats.address,
                    "direction": "inflow",
                    "amount": float(stats.total_inflow_tokens[mint]),
                    "tx_count": stats.total_transactions,
                })
            if mint in stats.total_outflow_tokens:
                flows.append({
                    "address": stats.address,
                    "direction": "outflow",
                    "amount": float(stats.total_outflow_tokens[mint]),
                    "tx_count": stats.total_transactions,
                })
        return flows
