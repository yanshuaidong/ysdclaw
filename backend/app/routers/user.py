from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.services.user import (
    get_users,
    get_user_by_username,
    create_user,
    update_user,
    delete_user,
)
from app.dependencies import require_admin
from app.models.user import User

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.get("", response_model=List[UserOut])
def list_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return get_users(db, skip, limit)


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def add_user(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在"
        )
    return create_user(db, user_data)


@router.put("/{user_id}", response_model=UserOut)
def edit_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    user = update_user(db, user_id, user_data)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
        )
    return user


@router.delete("/{user_id}")
def remove_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    if admin.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="不能删除自己"
        )
    if not delete_user(db, user_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在"
        )
    return {"detail": "删除成功"}
