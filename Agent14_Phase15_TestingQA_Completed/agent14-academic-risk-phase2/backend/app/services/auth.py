"""Compatibility wrapper around the centralized security/dependency layer."""
from app.core.security import hash_password, verify_password, create_access_token
from app.core.dependencies import get_current_user, require_roles
