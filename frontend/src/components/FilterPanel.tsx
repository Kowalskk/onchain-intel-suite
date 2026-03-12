import React from 'react';
import type { TraceFilters, TokenInfo } from '../types';

interface Props {
    filters: TraceFilters;
    onFiltersChange: (f: TraceFilters) => void;
    availableTokens: TokenInfo[];
    isLoading: boolean;
}

const label = (text: string) => (
    <span style={{ display: 'block', fontSize: '11px', fontFamily: 'JetBrains Mono, monospace', color: 'var(--sol-text-secondary)', marginBottom: '4px', letterSpacing: '0.05em', textTransform: 'uppercase' }}>
        {text}
    </span>
);

const select = (value: string, onChange: (v: string) => void, children: React.ReactNode) => (
    <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="input-base"
        style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '12px', height: '34px', cursor: 'pointer' }}
    >
        {children}
    </select>
);

export const FilterPanel: React.FC<Props> = ({ filters, onFiltersChange, availableTokens, isLoading }) => {
    const update = (partial: Partial<TraceFilters>) => onFiltersChange({ ...filters, ...partial });

    const handleDate = (field: 'fromDate' | 'toDate', val: string) => {
        const ts = val ? Math.floor(new Date(val).getTime() / 1000) : undefined;
        update({ [field]: ts });
    };

    const toDateStr = (ts?: number) => ts ? new Date(ts * 1000).toISOString().split('T')[0] : '';

    const reset = () =>
        onFiltersChange({ status: 'succeeded', tokenAccounts: 'balanceChanged' });

    return (
        <aside style={{
            background: 'var(--sol-bg-secondary)',
            border: '1px solid var(--sol-border)',
            borderRadius: '10px',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '14px',
            minWidth: '200px',
            maxWidth: '240px',
        }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <span style={{ fontSize: '12px', fontFamily: 'JetBrains Mono, monospace', fontWeight: 600, color: 'var(--sol-text-emphasis)', letterSpacing: '0.08em' }}>
                    FILTERS
                </span>
                <button onClick={reset} disabled={isLoading} style={{
                    fontSize: '10px', fontFamily: 'JetBrains Mono, monospace',
                    color: 'var(--sol-cyan)', background: 'none', border: 'none',
                    cursor: 'pointer', padding: '2px 4px',
                }}>
                    RESET
                </button>
            </div>

            {/* Date range */}
            <div>
                {label('Date range')}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <input type="date" value={toDateStr(filters.fromDate)} onChange={e => handleDate('fromDate', e.target.value)}
                        className="input-base" style={{ fontSize: '12px', height: '32px' }} />
                    <input type="date" value={toDateStr(filters.toDate)} onChange={e => handleDate('toDate', e.target.value)}
                        className="input-base" style={{ fontSize: '12px', height: '32px' }} />
                </div>
            </div>

            {/* Token filter */}
            <div>
                {label('Token')}
                {select(filters.token || '', v => update({ token: v || undefined }), (
                    <>
                        <option value="">All tokens</option>
                        <option value="SOL">SOL</option>
                        {availableTokens.map(t => (
                            <option key={t.mint} value={t.mint}>{t.symbol} · {t.mint.slice(0, 6)}…</option>
                        ))}
                    </>
                ))}
            </div>

            {/* Asset type */}
            <div>
                {label('Asset type')}
                {select(filters.tokenAccounts, v => update({ tokenAccounts: v as TraceFilters['tokenAccounts'] }), (
                    <>
                        <option value="balanceChanged">Balance changed</option>
                        <option value="all">All assets</option>
                        <option value="none">Direct only</option>
                    </>
                ))}
            </div>

            {/* Min amount */}
            <div>
                {label('Min amount')}
                <input
                    type="number"
                    value={filters.minAmount ?? ''}
                    onChange={e => update({ minAmount: e.target.value ? parseFloat(e.target.value) : undefined })}
                    placeholder="0"
                    min="0"
                    className="input-base"
                    style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: '12px', height: '32px' }}
                />
            </div>

            {/* Status */}
            <div>
                {label('Status')}
                {select(filters.status, v => update({ status: v as TraceFilters['status'] }), (
                    <>
                        <option value="succeeded">Succeeded</option>
                        <option value="failed">Failed</option>
                        <option value="any">Any</option>
                    </>
                ))}
            </div>
        </aside>
    );
};
