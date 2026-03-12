from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

from ...core.helius_client import HeliusClient
from ...core.graph_builder import GraphBuilder
from ...core.flow_analyzer import FlowAnalyzer
from ...core.transaction_parser import TransactionParser
from ...utils.known_addresses import get_label
from ...utils.token_metadata import (
    get_cached_metadata,
    set_cached_metadata,
    extract_symbol,
    extract_name,
)

router = APIRouter(prefix="/api/trace", tags=["trace"])


# ─── Request / Response Models ───────────────────────────────────────────────

class TraceRequest(BaseModel):
    address: str = Field(..., description="Wallet address to trace")
    depth: int = Field(default=1, ge=0, le=3, description="Expansion depth (0-3)")
    filters: Optional[Dict[str, Any]] = Field(default=None)


class ExpandNodeRequest(BaseModel):
    address: str
    root_address: str
    current_depth: int
    filters: Optional[Dict[str, Any]] = None


class NodeData(BaseModel):
    id: str
    label: str
    total_tx: int
    total_moves: int
    is_root: bool
    depth: int


class EdgeData(BaseModel):
    source: str
    target: str
    label: str
    amount_display: str
    token: str
    tx_count: int


class TraceResponse(BaseModel):
    nodes: List[NodeData]
    edges: List[EdgeData]
    root_address: str
    total_nodes: int
    total_edges: int
    filters_applied: Optional[Dict[str, Any]] = None


class FlowEntry(BaseModel):
    address: str
    label: Optional[str] = None
    direction: str  # "inflow" | "outflow"
    amount: str
    token: str
    tx_count: int
    first_seen: Optional[int] = None
    last_seen: Optional[int] = None


class FlowsResponse(BaseModel):
    address: str
    inflows: List[FlowEntry]
    outflows: List[FlowEntry]
    total_inflow_count: int
    total_outflow_count: int
    unique_tokens: List[str]


# ─── Endpoints ────────────────────────────────────────────────────────────────

@router.post("/full", response_model=TraceResponse)
async def trace_wallet(request: TraceRequest):
    """
    Realiza un trace completo de una wallet.
    Devuelve el grafo de nodos y edges para la visualización D3.
    """
    try:
        client = HeliusClient()
        builder = GraphBuilder(client, max_depth=request.depth)

        helius_filters = _build_helius_filters(request.filters)

        graph = await builder.build_trace_graph(
            root_address=request.address,
            filters=helius_filters,
        )

        await client.close()

        return TraceResponse(
            nodes=[_node_to_data(n) for n in graph.nodes],
            edges=[EdgeData(
                source=e.source,
                target=e.target,
                label=e.label,
                amount_display=e.amount_display,
                token=e.token,
                tx_count=e.tx_count,
            ) for e in graph.edges],
            root_address=graph.root_address,
            total_nodes=graph.total_nodes,
            total_edges=graph.total_edges,
            filters_applied=request.filters,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/expand", response_model=TraceResponse)
async def expand_node(request: ExpandNodeRequest):
    """
    Expande un nodo específico del grafo (expansión manual desde el frontend).
    """
    try:
        client = HeliusClient()
        builder = GraphBuilder(client, max_depth=1)

        helius_filters = _build_helius_filters(request.filters)

        graph = await builder.build_trace_graph(
            root_address=request.address,
            filters=helius_filters,
        )

        await client.close()

        return TraceResponse(
            nodes=[NodeData(
                id=n.id,
                label=n.label or _abbreviate(n.id),
                total_tx=n.total_tx,
                total_moves=n.total_moves,
                is_root=False,
                depth=n.depth + request.current_depth,
            ) for n in graph.nodes],
            edges=[EdgeData(
                source=e.source,
                target=e.target,
                label=e.label,
                amount_display=e.amount_display,
                token=e.token,
                tx_count=e.tx_count,
            ) for e in graph.edges],
            root_address=request.address,
            total_nodes=len(graph.nodes),
            total_edges=len(graph.edges),
            filters_applied=request.filters,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/flows/{address}", response_model=FlowsResponse)
async def get_wallet_flows(
    address: str,
    from_date: Optional[int] = Query(None, description="Unix timestamp start"),
    to_date: Optional[int] = Query(None, description="Unix timestamp end"),
    token: Optional[str] = Query(None, description="Token mint address filter"),
    min_amount: Optional[float] = Query(None, description="Minimum amount filter"),
):
    """
    Obtiene los flujos de una wallet con filtros opcionales.
    Devuelve listas separadas de inflows y outflows.
    """
    try:
        client = HeliusClient()

        filters: Dict[str, Any] = {"status": "succeeded", "tokenAccounts": "balanceChanged"}
        if from_date or to_date:
            filters["blockTime"] = {}
            if from_date:
                filters["blockTime"]["gte"] = from_date
            if to_date:
                filters["blockTime"]["lte"] = to_date

        transactions = await client.get_all_transactions(
            address=address,
            filters=filters,
            max_transactions=1000,
        )

        parser = TransactionParser(address)
        analyzer = FlowAnalyzer(address)

        for tx_data in transactions:
            parsed = parser.parse_transaction(tx_data)
            if parsed.success:
                analyzer.add_transaction(parsed)

        await client.close()

        summary = analyzer.get_summary()
        inflows: List[FlowEntry] = []
        outflows: List[FlowEntry] = []
        unique_tokens: set = {"SOL"}

        for cp in summary.top_inflow_counterparties:
            label = get_label(cp.address)
            if cp.total_inflow_sol > 0:
                inflows.append(FlowEntry(
                    address=cp.address,
                    label=label,
                    direction="inflow",
                    amount=f"{cp.total_inflow_sol:.4f}",
                    token="SOL",
                    tx_count=cp.total_transactions,
                    first_seen=cp.first_interaction,
                    last_seen=cp.last_interaction,
                ))
            for mint, amount in cp.total_inflow_tokens.items():
                if token and mint != token:
                    continue
                if min_amount and float(amount) < min_amount:
                    continue
                unique_tokens.add(mint)
                inflows.append(FlowEntry(
                    address=cp.address,
                    label=label,
                    direction="inflow",
                    amount=str(amount),
                    token=mint,
                    tx_count=cp.total_transactions,
                    first_seen=cp.first_interaction,
                    last_seen=cp.last_interaction,
                ))

        for cp in summary.top_outflow_counterparties:
            label = get_label(cp.address)
            if cp.total_outflow_sol > 0:
                outflows.append(FlowEntry(
                    address=cp.address,
                    label=label,
                    direction="outflow",
                    amount=f"{cp.total_outflow_sol:.4f}",
                    token="SOL",
                    tx_count=cp.total_transactions,
                    first_seen=cp.first_interaction,
                    last_seen=cp.last_interaction,
                ))
            for mint, amount in cp.total_outflow_tokens.items():
                if token and mint != token:
                    continue
                if min_amount and float(amount) < min_amount:
                    continue
                unique_tokens.add(mint)
                outflows.append(FlowEntry(
                    address=cp.address,
                    label=label,
                    direction="outflow",
                    amount=str(amount),
                    token=mint,
                    tx_count=cp.total_transactions,
                    first_seen=cp.first_interaction,
                    last_seen=cp.last_interaction,
                ))

        return FlowsResponse(
            address=address,
            inflows=inflows,
            outflows=outflows,
            total_inflow_count=len(inflows),
            total_outflow_count=len(outflows),
            unique_tokens=list(unique_tokens),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tokens/{address}")
async def get_wallet_tokens(address: str):
    """
    Obtiene la lista de tokens únicos con los que interactuó una wallet.
    Útil para el selector de filtro de tokens en el frontend.
    """
    try:
        client = HeliusClient()

        transactions = await client.get_all_transactions(
            address=address,
            filters={"status": "succeeded", "tokenAccounts": "balanceChanged"},
            max_transactions=500,
        )

        parser = TransactionParser(address)
        analyzer = FlowAnalyzer(address)

        for tx_data in transactions:
            parsed = parser.parse_transaction(tx_data)
            if parsed.success:
                analyzer.add_transaction(parsed)

        summary = analyzer.get_summary()
        tokens = []

        for mint in summary.unique_tokens:
            # Primero buscar en cache / tokens conocidos
            cached = get_cached_metadata(mint)
            if cached:
                tokens.append({"mint": mint, "symbol": cached.get("symbol", mint[:6]), "name": cached.get("name", "Unknown")})
                continue

            # Si no, consultar Helius DAS
            try:
                raw = await client.get_token_metadata(mint)
                symbol = extract_symbol(mint, raw)
                name = extract_name(mint, raw)
                set_cached_metadata(mint, {"symbol": symbol, "name": name})
                tokens.append({"mint": mint, "symbol": symbol, "name": name})
            except Exception:
                tokens.append({"mint": mint, "symbol": mint[:8], "name": "Unknown"})

        await client.close()
        return {"tokens": tokens}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _build_helius_filters(filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    base: Dict[str, Any] = {"status": "succeeded", "tokenAccounts": "balanceChanged"}
    if not filters:
        return base

    base["status"] = filters.get("status", "succeeded")
    base["tokenAccounts"] = filters.get("token_accounts", "balanceChanged")

    if filters.get("from_date") or filters.get("to_date"):
        base["blockTime"] = {}
        if filters.get("from_date"):
            base["blockTime"]["gte"] = filters["from_date"]
        if filters.get("to_date"):
            base["blockTime"]["lte"] = filters["to_date"]

    return base


def _node_to_data(n: Any) -> NodeData:
    return NodeData(
        id=n.id,
        label=get_label(n.id) or n.label or _abbreviate(n.id),
        total_tx=n.total_tx,
        total_moves=n.total_moves,
        is_root=n.is_root,
        depth=n.depth,
    )


def _abbreviate(address: str) -> str:
    if len(address) <= 8:
        return address
    return f"{address[:4]}...{address[-4:]}"
