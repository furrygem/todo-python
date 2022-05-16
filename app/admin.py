from fastapi import Depends, APIRouter
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session
from app import crud
from app.main import get_db
from app.internal.auth import verify_auth_token, register_user, bcrypt_password
from app.internal.schemas import UserDTOSchemaAdmin, UserFullSchema
from app.internal.schemas import UserPermissionsEnum, UserInsertSchema


admin_router = APIRouter(prefix="/api/admin")


def check_is_admin(token: dict[str, any], admin_permission: int) -> bool:
    """Check if token has admin permission

    Args:
        token (dict[str, any]): JWT decoded, verified token
        admin_permission (int): integer value that represents admin
            permissions in a token

    Returns:
        bool: _description_
    """
    permissions = token['permissions']
    if admin_permission not in permissions:
        return False
    return True


@admin_router.get('/api/admin/users', response_model=list[UserFullSchema])
def admin_list_users(offset: int = 0,
                     limit: int = 100,
                     username_filter: str = "",
                     db: Session = Depends(get_db),
                     token: dict[str, any] = Depends(verify_auth_token)):
    if not check_is_admin(token, UserPermissionsEnum.admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    if username_filter:
        user = crud.get_user_by_username(db, username_filter)
        return list(user)
    users = crud.list_users(db, offset, limit)
    return users


@admin_router.post('/api/admin/users', response_model=UserFullSchema)
def admin_insert_new_user(user: UserDTOSchemaAdmin,
                          db: Session = Depends(get_db),
                          token: dict[str, any] = Depends(verify_auth_token)):
    if not check_is_admin(token, UserPermissionsEnum.admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    user = register_user(db, **user.dict())
    return user


@admin_router.get('/api/admin/users/{user_id}')
def admin_get_user(user_id: int,
                   db: Session = Depends(get_db),
                   token: dict[str, any] = Depends(verify_auth_token)):
    if not check_is_admin(token, UserPermissionsEnum.admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    user = crud.get_user_by_id(db, user_id)
    return user


@admin_router.put('/api/admin/users/{user_id}', response_model=UserFullSchema)
def admin_update_user(user_id: int,
                      user_update: UserDTOSchemaAdmin,
                      db: Session = Depends(get_db),
                      token: dict[str, any] = Depends(verify_auth_token)):
    if not check_is_admin(token, UserPermissionsEnum.admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    if user_update.raw_password:
        user_update.password = bcrypt_password(user_update.raw_password)
        delattr(user_update, 'raw_password')

    update = UserInsertSchema(**user_update.dict())
    updated = crud.update_user(db, user_id, update)
    return updated


@admin_router.delete('/api/admin/users/{user_id}')
def admin_delete_user(user_id: int,
                      db: Session = Depends(get_db),
                      token: dict[str, any] = Depends(verify_auth_token)):
    if not check_is_admin(token, UserPermissionsEnum.admin):
        raise HTTPException(status_code=403, detail="Not authorized")
    removed = crud.delete_todo_by_id(db, user_id)
    if removed <= 0:
        raise HTTPException(status_code=400, detail="No user deleted")
    return
