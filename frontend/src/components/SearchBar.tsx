import React, { useState, useRef } from 'react';

interface Props {
    onSearch: (address: string) => void;
    isLoading?: boolean;
    placeholder?: string;
}

export const SearchBar: React.FC<Props> = ({
    onSearch,
    isLoading = false,
    placeholder = 'PASTE WALLET ADDRESS...',
}) => {
    const [value, setValue] = useState('');
    const inputRef = useRef<HTMLInputElement>(null);

    const handleSubmit = () => {
        const trimmed = value.trim();
        if (trimmed && !isLoading) onSearch(trimmed);
    };

    return (
        <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
            {/* Prompt symbol */}
            <span style={{
                position: 'absolute',
                left: '12px',
                fontFamily: 'JetBrains Mono, monospace',
                fontSize: '13px',
                color: 'var(--sol-text-secondary)',
                pointerEvents: 'none',
                userSelect: 'none',
            }}>
                {'>_'}
            </span>

            <input
                ref={inputRef}
                id="wallet-search"
                type="text"
                value={value}
                onChange={e => setValue(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                placeholder={placeholder}
                disabled={isLoading}
                style={{
                    width: '360px',
                    height: '38px',
                    paddingLeft: '36px',
                    paddingRight: '80px',
                    background: 'var(--sol-bg-primary)',
                    color: 'var(--sol-text-primary)',
                    border: '1px solid var(--sol-border-em)',
                    borderRadius: '8px',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '12px',
                    outline: 'none',
                    transition: 'border-color 0.15s',
                }}
                onFocus={e => (e.target.style.borderColor = 'var(--sol-cyan)')}
                onBlur={e => (e.target.style.borderColor = 'var(--sol-border-em)')}
            />

            {/* Search button / loader */}
            <button
                onClick={handleSubmit}
                disabled={isLoading || !value.trim()}
                style={{
                    position: 'absolute',
                    right: '6px',
                    height: '28px',
                    padding: '0 10px',
                    background: value.trim() && !isLoading ? 'var(--sol-cyan)' : 'var(--sol-bg-secondary)',
                    color: value.trim() && !isLoading ? 'var(--sol-bg-primary)' : 'var(--sol-text-secondary)',
                    border: 'none',
                    borderRadius: '5px',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: '11px',
                    fontWeight: 600,
                    cursor: value.trim() && !isLoading ? 'pointer' : 'default',
                    transition: 'background 0.15s, color 0.15s',
                    letterSpacing: '0.05em',
                }}
            >
                {isLoading ? (
                    <span className="animate-spin-slow" style={{ display: 'inline-block' }}>⟳</span>
                ) : 'TRACE'}
            </button>
        </div>
    );
};
