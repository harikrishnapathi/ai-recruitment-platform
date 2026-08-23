import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.membership import Membership, MembershipRole


RECRUITER_WRITE_ROLES = {
    MembershipRole.OWNER,
    MembershipRole.ADMIN,
    MembershipRole.RECRUITER,
    MembershipRole.HIRING_MANAGER,
}


def require_membership(
    db: Session,
    user_id: uuid.UUID,
    organization_id: uuid.UUID,
    allowed_roles: set[MembershipRole] | None = None,
) -> Membership:
    membership = db.scalar(
        select(Membership).where(
            Membership.user_id == user_id,
            Membership.organization_id == organization_id,
        )
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this organization.",
        )
    if allowed_roles and membership.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission for this action.",
        )
    return membership
