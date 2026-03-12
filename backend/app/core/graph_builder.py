from typing import List, Dict, Any, Set, Optional
from dataclasses import dataclass, field
from decimal import Decimal
import asyncio

from .flow_analyzer import FlowAnalyzer, CounterpartyStats
from .helius_client import HeliusClient
from .transaction_parser import TransactionParser


@dataclass
class GraphNode:
    """Nodo del grafo representando una wallet."""
    id: str
    label: Optional[str] = None
    total_tx: int = 0
    total_moves: int = 0
    is_root: bool = False
    depth: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    """Arista representando flujo entre wallets."""
    source: str
    target: str
    label: str          # "19.6k USDC · 8 tx"
    amount_display: str
    token: str
    tx_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TraceGraph:
    """Grafo completo de trazabilidad."""
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    root_address: str
    total_nodes: int
    total_edges: int


class GraphBuilder:
    """
    Construye el grafo de trazabilidad expandiendo
    recursivamente las contrapartes más relevantes.
    """

    def __init__(self, helius_client: HeliusClient, max_depth: int = 2):
        self.client = helius_client
        self.max_depth = max_depth
        self.visited: Set[str] = set()
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []

    async def build_trace_graph(
        self,
        root_address: str,
        filters: Optional[Dict[str, Any]] = None,
        expand_addresses: Optional[List[str]] = None,
    ) -> TraceGraph:
        """Construye el grafo desde una dirección raíz."""
        self.visited.clear()
        self.nodes.clear()
        self.edges.clear()

        self.nodes[root_address] = GraphNode(
            id=root_address,
            label=self._abbreviate_address(root_address),
            is_root=True,
            depth=0,
        )

        await self._process_address(root_address, 0, filters)

        if expand_addresses:
            for addr in expand_addresses:
                if addr not in self.visited and addr in self.nodes:
                    await self._process_address(addr, self.nodes[addr].depth, filters)

        return TraceGraph(
            nodes=list(self.nodes.values()),
            edges=self.edges,
            root_address=root_address,
            total_nodes=len(self.nodes),
            total_edges=len(self.edges),
        )

    async def _process_address(
        self,
        address: str,
        current_depth: int,
        filters: Optional[Dict[str, Any]] = None,
    ):
        """Procesa una dirección: fetch txs → parse → analizar → crear nodos/edges."""
        if address in self.visited:
            return
        self.visited.add(address)

        transactions = await self.client.get_all_transactions(
            address=address,
            filters=filters,
            max_transactions=500,
        )

        parser = TransactionParser(address)
        analyzer = FlowAnalyzer(address)

        for tx_data in transactions:
            parsed = parser.parse_transaction(tx_data)
            if parsed.success:
                analyzer.add_transaction(parsed)

        # Actualizar nodo existente
        if address in self.nodes:
            self.nodes[address].total_tx = len(transactions)
            self.nodes[address].total_moves = len(analyzer.counterparties)

        # Crear nodos de contrapartes y edges
        for counterparty_address, stats in analyzer.counterparties.items():
            if counterparty_address not in self.nodes:
                self.nodes[counterparty_address] = GraphNode(
                    id=counterparty_address,
                    label=self._abbreviate_address(counterparty_address),
                    total_tx=stats.total_transactions,
                    total_moves=1,
                    depth=current_depth + 1,
                )
            self._create_edges_from_stats(address, counterparty_address, stats)

        # Expandir recursivamente hasta max_depth
        if current_depth < self.max_depth:
            summary = analyzer.get_summary()
            top_addresses = [
                cp.address for cp in summary.top_inflow_counterparties[:5]
            ] + [
                cp.address for cp in summary.top_outflow_counterparties[:5]
            ]

            for cp_address in set(top_addresses):
                if cp_address not in self.visited:
                    await self._process_address(cp_address, current_depth + 1, filters)
                    await asyncio.sleep(0.1)

    def _create_edges_from_stats(
        self, source: str, target: str, stats: CounterpartyStats
    ):
        """Crea edges de SOL y tokens basados en stats de contraparte."""
        # SOL edge
        if stats.total_inflow_sol > 0 or stats.total_outflow_sol > 0:
            net_sol = stats.total_inflow_sol - stats.total_outflow_sol
            direction = "inflow" if net_sol > 0 else "outflow"
            edge_source = target if direction == "inflow" else source
            edge_target = source if direction == "inflow" else target

            self.edges.append(GraphEdge(
                source=edge_source,
                target=edge_target,
                label=self._format_amount_label(abs(net_sol), "SOL", stats.total_transactions),
                amount_display=self._format_amount(abs(net_sol)),
                token="SOL",
                tx_count=stats.total_transactions,
            ))

        # Token edges
        all_mints = set(stats.total_inflow_tokens.keys()) | set(stats.total_outflow_tokens.keys())
        for mint in all_mints:
            inflow = stats.total_inflow_tokens.get(mint, Decimal(0))
            outflow = stats.total_outflow_tokens.get(mint, Decimal(0))
            net = inflow - outflow

            if net == 0:
                continue

            direction = "inflow" if net > 0 else "outflow"
            edge_source = target if direction == "inflow" else source
            edge_target = source if direction == "inflow" else target
            token_label = mint[:4] + "..."

            self.edges.append(GraphEdge(
                source=edge_source,
                target=edge_target,
                label=self._format_amount_label(abs(net), token_label, stats.total_transactions),
                amount_display=self._format_amount(abs(net)),
                token=mint,
                tx_count=stats.total_transactions,
            ))

    def _abbreviate_address(self, address: str) -> str:
        if len(address) <= 8:
            return address
        return f"{address[:4]}...{address[-4:]}"

    def _format_amount(self, amount: Decimal) -> str:
        if amount >= 1_000_000:
            return f"{amount / 1_000_000:.1f}M"
        elif amount >= 1_000:
            return f"{amount / 1_000:.1f}k"
        else:
            return f"{amount:.2f}"

    def _format_amount_label(self, amount: Decimal, token: str, tx_count: int) -> str:
        return f"{self._format_amount(amount)} {token} · {tx_count} tx"
