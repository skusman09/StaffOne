"""
Transaction management — declarative transaction boundaries for service methods.

Provides a @transactional decorator that wraps service methods with
commit-on-success / rollback-on-failure semantics.

Design rules:
- The decorator expects `self.db` to be a SQLAlchemy Session on the service instance
- Nested @transactional calls are safe: only the outermost transaction commits
- HTTPException is re-raised without rollback (it's a business error, not a crash)

Usage:
    class LeaveService:
        @transactional
        def approve_leave(self, leave_id: int, admin_user: User) -> Leave:
            # Just do your work — no manual commit/rollback needed
            leave = self.repo.get_by_id(leave_id)
            leave.status = LeaveStatus.APPROVED
            return leave  # auto-committed on success
"""
import logging
import functools
from typing import TypeVar, Callable, Any

from fastapi import HTTPException

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])

# Sentinel attribute to track if we're already inside a transaction
_TXN_ACTIVE_ATTR = "_txn_active"


def transactional(func: F) -> F:
    """Decorator that wraps a service method in a database transaction.

    Commits on success, rolls back on unhandled exceptions.
    HTTPExceptions are considered business errors and are re-raised
    without rollback (they represent expected validation failures,
    not system errors).

    Handles nesting: if already inside a @transactional call on the
    same db session, the inner call becomes a no-op (the outer
    transaction will commit).
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        db = getattr(self, "db", None)
        if db is None:
            raise RuntimeError(
                f"@transactional requires 'self.db' (SQLAlchemy Session) on {type(self).__name__}"
            )

        # Check if we're already in a transaction (nested @transactional call)
        already_in_txn = getattr(db, _TXN_ACTIVE_ATTR, False)
        if already_in_txn:
            # Nested call — just execute, let the outer transaction handle commit
            return func(self, *args, **kwargs)

        # Mark transaction as active
        setattr(db, _TXN_ACTIVE_ATTR, True)
        try:
            result = func(self, *args, **kwargs)
            db.commit()
            return result
        except HTTPException:
            # Business error (400, 404, etc.) — don't rollback, just re-raise.
            # The session state is still valid; the caller may catch and retry.
            # But we do need to clear the transaction marker.
            raise
        except Exception:
            db.rollback()
            raise
        finally:
            setattr(db, _TXN_ACTIVE_ATTR, False)

    return wrapper  # type: ignore[return-value]


class TransactionContext:
    """Context manager alternative for cases where decorator isn't suitable.

    Usage:
        with TransactionContext(db):
            db.add(some_record)
            db.add(another_record)
        # auto-committed on exit, rolled back on exception
    """

    def __init__(self, db):
        self.db = db

    def __enter__(self):
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.db.commit()
        elif issubclass(exc_type, HTTPException):
            # Business error — don't rollback
            pass
        else:
            self.db.rollback()
        return False  # Don't suppress exceptions
