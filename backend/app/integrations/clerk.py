"""
Clerk authentication integration
"""

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

async def verify_token(token: str) -> str:
    """
    Clerk 토큰 검증 및 사용자 ID 반환

    Args:
        token: JWT token from Clerk

    Returns:
        user_id: Clerk user ID

    Raises:
        Exception: If token is invalid
    """
    try:
        # TODO: Implement proper Clerk SDK token verification
        # For now, this is a placeholder
        # In production, use: clerk_sdk.verify_token(token)

        # Placeholder implementation
        # You should use the official Clerk SDK here
        if not token:
            raise ValueError("Token is required")

        # Mock user ID extraction (replace with actual implementation)
        user_id = "mock_user_id"

        return user_id

    except Exception as e:
        logger.error(f"Clerk token verification failed: {str(e)}")
        raise
