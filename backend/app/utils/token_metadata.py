"""
Cache simple en memoria de metadata de tokens.
Evita llamadas repetidas a la API de Helius para el mismo mint.
"""

from typing import Dict, Any, Optional


_cache: Dict[str, Dict[str, Any]] = {}

# Tokens populares con metadata hardcodeada para respuesta inmediata
WELL_KNOWN_TOKENS: Dict[str, Dict[str, str]] = {
    "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v": {"symbol": "USDC", "name": "USD Coin"},
    "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB": {"symbol": "USDT", "name": "Tether USD"},
    "So11111111111111111111111111111111111111112": {"symbol": "wSOL", "name": "Wrapped SOL"},
    "mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So": {"symbol": "mSOL", "name": "Marinade Staked SOL"},
    "7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs": {"symbol": "ETH", "name": "Ethereum (Wormhole)"},
    "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263": {"symbol": "BONK", "name": "Bonk"},
    "JUPyiwrYJFskUPiHa7hkeR8VUtAeFoSYbKedZNsDvCN": {"symbol": "JUP", "name": "Jupiter"},
    "27G8MtK7VtTcCHkpASjSDdkWWYfoqT6ggEuKidVJidD4": {"symbol": "JLP", "name": "Jupiter Liquidity Pool"},
    "HZ1JovNiVvGrGs7iBV2xAtojfkCPm6rEBcJFnqiGGp9": {"symbol": "PYTH", "name": "Pyth Network"},
    "hntyVP6YFm1Hg25TN9WGLqM12b8TQmcknKrdu1oxWux": {"symbol": "HNT", "name": "Helium"},
    "mb1eu7TzEc71KxDpsmsKoucSSuuoGLv1drys1oP2jh6": {"symbol": "MOBILE", "name": "Helium Mobile"},
    "iotEVVZLEywoTn1QdwNPddxPWszn3zFhEot3MfL9fns": {"symbol": "IOT", "name": "Helium IoT"},
    "4k3Dyjzvzp8eMZWUXbBCjEvwSkkk59S5iCNLY3QrkX6R": {"symbol": "RAY", "name": "Raydium"},
    "SRMuApVNdxXokk5GT7XD5cUUgXMBCoAz2LHeuAoKWRt": {"symbol": "SRM", "name": "Serum"},
    "7xKXtg2CW87d97TXJSDpbD5jBkheTqA83TZRuJosgAsU": {"symbol": "SAMO", "name": "Samoyedcoin"},
    "MNDEFzGvMt87ueuHvVU9VcTqsAP5b3fTGPsHuuPA5ey": {"symbol": "MNDE", "name": "Marinade"},
}


def get_cached_metadata(mint: str) -> Optional[Dict[str, Any]]:
    """Retorna metadata cacheada si existe."""
    if mint in WELL_KNOWN_TOKENS:
        return WELL_KNOWN_TOKENS[mint]
    return _cache.get(mint)


def set_cached_metadata(mint: str, metadata: Dict[str, Any]):
    """Guarda metadata en cache."""
    _cache[mint] = metadata


def extract_symbol(mint: str, raw_metadata: Dict[str, Any]) -> str:
    """Extrae el símbolo de la respuesta raw de getAsset."""
    try:
        content = raw_metadata.get("result", {}).get("content", {})
        symbol = content.get("metadata", {}).get("symbol", "")
        if symbol:
            return symbol
    except Exception:
        pass
    return mint[:6]


def extract_name(mint: str, raw_metadata: Dict[str, Any]) -> str:
    """Extrae el nombre de la respuesta raw de getAsset."""
    try:
        content = raw_metadata.get("result", {}).get("content", {})
        name = content.get("metadata", {}).get("name", "")
        if name:
            return name
    except Exception:
        pass
    return "Unknown Token"
