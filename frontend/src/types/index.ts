// ─── Graph Types ──────────────────────────────────────────────────────────────

export interface GraphNode {
    id: string;
    label: string;
    totalTx: number;
    totalMoves: number;
    isRoot: boolean;
    depth: number;
    // D3 simulation properties
    x?: number;
    y?: number;
    fx?: number | null;
    fy?: number | null;
}

export interface GraphEdge {
    source: string | GraphNode;
    target: string | GraphNode;
    label: string;
    amountDisplay: string;
    token: string;
    txCount: number;
}

export interface TraceGraph {
    nodes: GraphNode[];
    edges: GraphEdge[];
    rootAddress: string;
    totalNodes: number;
    totalEdges: number;
}

// ─── Flow Types ───────────────────────────────────────────────────────────────

export interface FlowEntry {
    address: string;
    label?: string;
    direction: 'inflow' | 'outflow';
    amount: string;
    token: string;
    txCount: number;
    firstSeen?: number;
    lastSeen?: number;
}

export interface FlowsData {
    address: string;
    inflows: FlowEntry[];
    outflows: FlowEntry[];
    totalInflowCount: number;
    totalOutflowCount: number;
    uniqueTokens: string[];
}

// ─── Filter Types ─────────────────────────────────────────────────────────────

export interface TraceFilters {
    fromDate?: number;
    toDate?: number;
    token?: string;
    minAmount?: number;
    status: 'succeeded' | 'failed' | 'any';
    tokenAccounts: 'none' | 'balanceChanged' | 'all';
}

// ─── Token Types ──────────────────────────────────────────────────────────────

export interface TokenInfo {
    mint: string;
    symbol: string;
    name: string;
}

// ─── API Request / Response ───────────────────────────────────────────────────

export interface TraceRequest {
    address: string;
    depth: number;
    filters?: Partial<TraceFilters>;
}

export interface ExpandNodeRequest {
    address: string;
    rootAddress: string;
    currentDepth: number;
    filters?: Partial<TraceFilters>;
}

// ─── App State ────────────────────────────────────────────────────────────────

export type Theme = 'light' | 'dark';

export interface AppState {
    searchAddress: string;
    graph: TraceGraph | null;
    flows: FlowsData | null;
    tokens: TokenInfo[];
    filters: TraceFilters;
    selectedNode: string | null;
    isLoading: boolean;
    error: string | null;
}
