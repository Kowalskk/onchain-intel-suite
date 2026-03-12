import { useState, useCallback } from 'react';
import { traceApi } from '../services/api';
import type { TraceGraph, FlowsData, TokenInfo, TraceFilters } from '../types';

const DEFAULT_FILTERS: TraceFilters = {
    status: 'succeeded',
    tokenAccounts: 'balanceChanged',
};

export function useTrace() {
    const [address, setAddress] = useState('');
    const [graph, setGraph] = useState<TraceGraph | null>(null);
    const [flows, setFlows] = useState<FlowsData | null>(null);
    const [tokens, setTokens] = useState<TokenInfo[]>([]);
    const [filters, setFilters] = useState<TraceFilters>(DEFAULT_FILTERS);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const trace = useCallback(async (walletAddress: string, depth = 1) => {
        if (!walletAddress.trim()) return;
        setAddress(walletAddress);
        setIsLoading(true);
        setError(null);

        try {
            // Fetch graph and flows in parallel
            const [graphData, flowsData] = await Promise.all([
                traceApi.traceWallet({ address: walletAddress, depth, filters }),
                traceApi.getFlows(walletAddress, {
                    fromDate: filters.fromDate,
                    toDate: filters.toDate,
                    token: filters.token,
                    minAmount: filters.minAmount,
                }),
            ]);

            setGraph(graphData);
            setFlows(flowsData);

            // Fetch token list separately (non-blocking)
            traceApi.getWalletTokens(walletAddress)
                .then(setTokens)
                .catch(() => {/* silent */ });

        } catch (err) {
            const msg = err instanceof Error ? err.message : 'An error occurred';
            setError(msg);
        } finally {
            setIsLoading(false);
        }
    }, [filters]);

    const reset = useCallback(() => {
        setAddress('');
        setGraph(null);
        setFlows(null);
        setTokens([]);
        setError(null);
        setFilters(DEFAULT_FILTERS);
    }, []);

    return {
        address,
        graph,
        flows,
        tokens,
        filters,
        setFilters,
        isLoading,
        error,
        trace,
        reset,
    };
}
