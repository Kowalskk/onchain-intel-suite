import axios from 'axios';
import type {
    TraceGraph,
    FlowsData,
    TraceRequest,
    ExpandNodeRequest,
    TokenInfo,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || '';

const api = axios.create({
    baseURL: API_BASE,
    timeout: 120_000, // 2 min for large traces
});

function mapNode(n: Record<string, unknown>) {
    return {
        id: n.id as string,
        label: n.label as string,
        totalTx: n.total_tx as number,
        totalMoves: n.total_moves as number,
        isRoot: n.is_root as boolean,
        depth: n.depth as number,
    };
}

function mapEdge(e: Record<string, unknown>) {
    return {
        source: e.source as string,
        target: e.target as string,
        label: e.label as string,
        amountDisplay: e.amount_display as string,
        token: e.token as string,
        txCount: e.tx_count as number,
    };
}

function mapFlow(f: Record<string, unknown>) {
    return {
        address: f.address as string,
        label: f.label as string | undefined,
        direction: f.direction as 'inflow' | 'outflow',
        amount: f.amount as string,
        token: f.token as string,
        txCount: f.tx_count as number,
        firstSeen: f.first_seen as number | undefined,
        lastSeen: f.last_seen as number | undefined,
    };
}

export const traceApi = {
    /** Full wallet trace → returns graph of nodes and edges */
    async traceWallet(request: TraceRequest): Promise<TraceGraph> {
        const { data } = await api.post('/api/trace/full', {
            address: request.address,
            depth: request.depth,
            filters: request.filters
                ? {
                    from_date: request.filters.fromDate,
                    to_date: request.filters.toDate,
                    token: request.filters.token,
                    min_amount: request.filters.minAmount,
                    status: request.filters.status,
                    token_accounts: request.filters.tokenAccounts,
                }
                : undefined,
        });

        return {
            nodes: data.nodes.map(mapNode),
            edges: data.edges.map(mapEdge),
            rootAddress: data.root_address,
            totalNodes: data.total_nodes,
            totalEdges: data.total_edges,
        };
    },

    /** Expand a single node to reveal its counterparties */
    async expandNode(request: ExpandNodeRequest): Promise<TraceGraph> {
        const { data } = await api.post('/api/trace/expand', {
            address: request.address,
            root_address: request.rootAddress,
            current_depth: request.currentDepth,
            filters: request.filters,
        });

        return {
            nodes: data.nodes.map(mapNode),
            edges: data.edges.map(mapEdge),
            rootAddress: data.root_address,
            totalNodes: data.total_nodes,
            totalEdges: data.total_edges,
        };
    },

    /** Get inflow / outflow list with optional filters */
    async getFlows(
        address: string,
        filters?: {
            fromDate?: number;
            toDate?: number;
            token?: string;
            minAmount?: number;
        }
    ): Promise<FlowsData> {
        const params = new URLSearchParams();
        if (filters?.fromDate) params.set('from_date', String(filters.fromDate));
        if (filters?.toDate) params.set('to_date', String(filters.toDate));
        if (filters?.token) params.set('token', filters.token);
        if (filters?.minAmount) params.set('min_amount', String(filters.minAmount));

        const { data } = await api.get(`/api/trace/flows/${address}?${params}`);

        return {
            address: data.address,
            inflows: data.inflows.map(mapFlow),
            outflows: data.outflows.map(mapFlow),
            totalInflowCount: data.total_inflow_count,
            totalOutflowCount: data.total_outflow_count,
            uniqueTokens: data.unique_tokens,
        };
    },

    /** Get unique token list for the filter dropdown */
    async getWalletTokens(address: string): Promise<TokenInfo[]> {
        const { data } = await api.get(`/api/trace/tokens/${address}`);
        return data.tokens as TokenInfo[];
    },
};
