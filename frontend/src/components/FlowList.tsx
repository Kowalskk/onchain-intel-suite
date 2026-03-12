import React, { useState } from 'react';
import type { FlowEntry } from '../types';

interface Props {
    inflows: FlowEntry[];
    outflows: FlowEntry[];
    onAddressClick: (address: string) => void;
}

function formatAmount(amount: string, token: string) {
    const num = parseFloat(amount);
    if (isNaN(num)) return `${amount} ${token}`;
    if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(2)}M ${token}`;
    if (num >= 1_000) return `${(num / 1_000).toFixed(2)}k ${token}`;
    return `${num.toFixed(4)} ${token}`;
}

function shortAddr(addr: string) {
    if (addr.length <= 8) return addr;
    return `${addr.slice(0, 4)}...${addr.slice(-4)}`;
}

function formatToken(mint: string) {
    if (mint === 'SOL') return 'SOL';
    return mint.length > 8 ? `${mint.slice(0, 4)}…` : mint;
}

export const FlowList: React.FC<Props> = ({ inflows, outflows, onAddressClick }) => {
    const [activeTab, setActiveTab] = useState<'outflow' | 'inflow'>('outflow');
    const flows = activeTab === 'inflow' ? inflows : outflows;
    const color = activeTab === 'inflow' ? 'var(--sol-green)' : 'var(--sol-red)';

    return (
        <div style={{
            background: 'var(--sol-bg-secondary)',
            border: '1px solid var(--sol-border)',
            borderRadius: '10px',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            minWidth: '220px',
        }}>
            {/* Tabs */}
            <div style={{ display: 'flex', borderBottom: '1px solid var(--sol-border)' }}>
                {(['outflow', 'inflow'] as const).map(tab => {
                    const count = tab === 'inflow' ? inflows.length : outflows.length;
                    const tabColor = tab === 'inflow' ? 'var(--sol-green)' : 'var(--sol-red)';
                    const isActive = activeTab === tab;
                    return (
                        <button
                            key={tab}
                            id={`tab-${tab}`}
                            onClick={() => setActiveTab(tab)}
                            style={{
                                flex: 1,
                                padding: '10px 4px',
                                background: isActive ? 'var(--sol-bg-primary)' : 'transparent',
                                border: 'none',
                                borderBottom: isActive ? `2px solid ${tabColor}` : '2px solid transparent',
                                cursor: 'pointer',
                                fontFamily: 'JetBrains Mono, monospace',
                                fontSize: '11px',
                                fontWeight: 600,
                                color: isActive ? tabColor : 'var(--sol-text-secondary)',
                                letterSpacing: '0.05em',
                                transition: 'all 0.15s',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '6px',
                            }}
                        >
                            <span>{tab === 'inflow' ? '←' : '→'}</span>
                            {tab.toUpperCase()}
                            <span style={{
                                background: isActive ? tabColor : 'var(--sol-border-em)',
                                color: isActive ? 'var(--sol-bg-primary)' : 'var(--sol-text-secondary)',
                                borderRadius: '10px',
                                padding: '1px 6px',
                                fontSize: '10px',
                            }}>
                                {count}
                            </span>
                        </button>
                    );
                })}
            </div>

            {/* Flow items */}
            <div style={{
                overflowY: 'auto',
                maxHeight: 'calc(100vh - 220px)',
                flex: 1,
            }}>
                {flows.length === 0 ? (
                    <div style={{
                        padding: '32px 16px',
                        textAlign: 'center',
                        color: 'var(--sol-text-secondary)',
                        fontFamily: 'JetBrains Mono, monospace',
                        fontSize: '11px',
                    }}>
                        No {activeTab}s found
                    </div>
                ) : (
                    flows.map((flow, i) => (
                        <div
                            key={`${flow.address}-${flow.token}-${i}`}
                            onClick={() => onAddressClick(flow.address)}
                            style={{
                                padding: '10px 14px',
                                borderBottom: '1px solid var(--sol-border)',
                                cursor: 'pointer',
                                transition: 'background 0.1s',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '3px',
                            }}
                            onMouseEnter={e => (e.currentTarget.style.background = 'var(--sol-bg-primary)')}
                            onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                        >
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                                <span style={{
                                    fontFamily: 'JetBrains Mono, monospace',
                                    fontSize: '12px',
                                    color: 'var(--sol-text-primary)',
                                }}>
                                    {flow.label || shortAddr(flow.address)}
                                </span>
                                <span style={{
                                    fontFamily: 'JetBrains Mono, monospace',
                                    fontSize: '11px',
                                    color,
                                    fontWeight: 600,
                                }}>
                                    {formatAmount(flow.amount, formatToken(flow.token))}
                                </span>
                            </div>
                            <div style={{
                                fontSize: '10px',
                                color: 'var(--sol-text-secondary)',
                                fontFamily: 'JetBrains Mono, monospace',
                                display: 'flex',
                                gap: '8px',
                            }}>
                                {flow.label && (
                                    <span style={{ color: 'var(--sol-text-secondary)' }}>{shortAddr(flow.address)}</span>
                                )}
                                <span>· {flow.txCount} tx</span>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};
