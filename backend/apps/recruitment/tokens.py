"""
US-21-T1: Secure Unique Link and Token Strategy
Provides cryptographic token generation, validation, expiration, and URL building utilities
for CareerFlow recruitment room shareable application links.
"""

import secrets
from typing import Tuple, Optional
from django.utils import timezone
from django.conf import settings
from .models import RecruitmentRoom


def generate_secure_share_token(nbytes: int = 16) -> str:
    """
    Generates a cryptographically secure, URL-safe random token.
    Uses 16 bytes by default, producing ~22 URL-safe characters.
    """
    return secrets.token_urlsafe(nbytes)


def is_token_expired(room: RecruitmentRoom) -> bool:
    """
    Checks if a room's share link has expired based on link_expires_at timestamp.
    """
    if room.link_expires_at is None:
        return False
    return timezone.now() > room.link_expires_at


def validate_share_token(token: str) -> Tuple[bool, Optional[RecruitmentRoom], Optional[str], int]:
    """
    Validates a share token for public candidate access.
    
    Returns:
        (is_valid: bool, room: RecruitmentRoom | None, error_message: str | None, status_code: int)
        
    Status codes:
        - 200: Valid and active
        - 404: Token not found
        - 410: Deactivated or expired or closed room
    """
    if not token or not token.strip():
        return False, None, "Application token was not provided.", 404

    try:
        room = RecruitmentRoom.objects.get(share_token=token.strip())
    except RecruitmentRoom.DoesNotExist:
        return False, None, "The requested application link does not exist or is invalid.", 404

    # Check if link has been explicitly deactivated by HR
    if not room.link_is_active:
        return False, room, "This application link has been deactivated by the hiring manager.", 410

    # Check if link has expired
    if is_token_expired(room):
        return False, room, "This application link has expired and is no longer accepting submissions.", 410

    # Check room operational status
    if room.status == 'CLOSED':
        return False, room, "This recruitment opening is currently closed.", 410

    return True, room, None, 200


def build_share_url(token: str, request=None) -> str:
    """
    Constructs the absolute or relative public application URL for candidate access.
    Prefers frontend client origin (port 5173 in development) if available.
    """
    relative_path = f"/apply/{token}"
    if request:
        origin = request.headers.get('Origin') or request.headers.get('Referer')
        if origin:
            from urllib.parse import urlparse
            parsed = urlparse(origin)
            return f"{parsed.scheme}://{parsed.netloc}{relative_path}"
        return request.build_absolute_uri(relative_path)
    return relative_path
