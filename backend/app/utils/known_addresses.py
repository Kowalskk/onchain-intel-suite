"""
Addresses conocidas de CEXs, DEXs y protocolos en Solana.
Se usan para añadir labels legibles a los nodos del grafo.
"""

KNOWN_ADDRESSES: dict[str, str] = {
    # Exchanges centralizados
    "5tzFkiKscXHK5ZXCGbXZxdw7gJLFHmb4oCQ7sJJMEKSs": "Binance",
    "AC5RDfQFmDS1deWZos921JfqscXdByf8BKHs5ACWjtW2": "Binance Hot Wallet",
    "GJRs4FwHtemZ5ZE9x3FNvJ8TMwitKTh21yxdRPqn7npE": "Coinbase",
    "H8sMJSCQxfKiFTCfDR3DUMLPwcRbM61LGFJ8N4dKi1QZ": "Coinbase 2",
    "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM": "Kraken",
    "FWznbcNXWQuHTawe9RxvQ2LdCyNAyph5haUEMwBNTLif": "OKX",
    "2AQdpHJ2JpcEgPiATUXjQxA8QmafFegfQwSLWSprPicm": "Bybit",

    # DEXs y protocolos
    "675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8": "Raydium AMM",
    "27haf8L6oxUeXrHrgEgsexjSY5hbVUWEmvv9Nyxg8vQv": "Raydium CLMM",
    "JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4": "Jupiter v6",
    "JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB": "Jupiter v4",
    "srmqPvymJeFKQ4zGQed1GFppgkRHL9kaELCbyksJtPX": "Serum DEX",
    "MarBmsSgKXdrN1egZf5sqe1TMai9K1rChYNDJgjq7aD": "Marinade Finance",
    "So11111111111111111111111111111111111111112": "Wrapped SOL",
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": "USDC Mint",
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": "USDT Mint",
    "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So": "mSOL Mint",

    # Programas conocidos
    "11111111111111111111111111111111": "System Program",
    "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA": "Token Program",
    "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJe1brs": "Associated Token Program",
    "ComputeBudget111111111111111111111111111111": "Compute Budget Program",
    "Vote111111111111111111111111111111111111111p": "Vote Program",
}


def get_label(address: str) -> str | None:
    """Retorna el label conocido para una dirección, o None."""
    return KNOWN_ADDRESSES.get(address)
