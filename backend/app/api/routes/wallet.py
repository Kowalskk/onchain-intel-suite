from fastapi import APIRouter

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


@router.get("/{address}/info")
async def get_wallet_info(address: str):
    """
    Información básica de una wallet.
    Placeholder — se puede expandir con balance SOL, token count, etc.
    """
    return {
        "address": address,
        "label": None,
        "note": "Detailed wallet info endpoint — coming soon",
    }
