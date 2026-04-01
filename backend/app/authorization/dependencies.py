"""
Authorization dependency factories for FastAPI.

Provides Depends()-compatible callables that enforce authorization
at the route level. These replace the scattered role checks in route handlers.

Usage:
    @router.get("/admin/users")
    def get_users(
        current_user: User = Depends(require(Permission.VIEW_ANY_USER))
    ):
        ...

    @router.post("/admin/generate")
    def generate_payroll(
        current_user: User = Depends(require(Permission.GENERATE_PAYROLL))
    ):
        ...
"""
from fastapi import Depends, HTTPException, status

from app.models.user import User
from app.utils.dependencies import get_current_user
from app.authorization.permissions import Permission, has_permission
from app.authorization.policies import PolicyViolation


def require(*permissions: Permission):
    """FastAPI dependency factory: require one or more permissions.

    Creates a Depends()-compatible callable that checks the current user
    has ALL of the specified permissions.

    Args:
        *permissions: One or more Permission values required

    Returns:
        A FastAPI dependency that returns the current User if authorized

    Usage:
        @router.get("/admin/users")
        def get_users(user: User = Depends(require(Permission.VIEW_ANY_USER))):
            ...

        @router.post("/admin/salary")
        def create(user: User = Depends(
            require(Permission.MANAGE_SALARY_CONFIG, Permission.VIEW_ANY_SALARY)
        )):
            ...
    """

    def _checker(current_user: User = Depends(get_current_user)) -> User:
        for perm in permissions:
            if not has_permission(current_user.role, perm):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: requires {perm.value}",
                )
        return current_user

    return _checker


def handle_policy_violation(exc: PolicyViolation) -> HTTPException:
    """Convert a PolicyViolation to an HTTPException.

    Use this in route handlers that call policy functions directly:

        try:
            policies.require_permission(user, Permission.GENERATE_PAYROLL)
        except PolicyViolation as e:
            raise handle_policy_violation(e)
    """
    return HTTPException(
        status_code=exc.status_code,
        detail=exc.message,
    )
