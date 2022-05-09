from datetime import datetime, timedelta
from sqlite3 import IntegrityError
from typing import List
from sqlalchemy.orm import Session
from app.models import RefreshToken, Todo, User
from app.schemas import TodoCreateSchema, TodoUpdateSchema, UserInsertSchema


def get_todos(db: Session, offset: int, limit: int) -> List[Todo]:
    result = db.query(Todo).offset(offset).limit(limit).all()
    return result


def get_todos_for_user(db: Session, offset: int, limit: int, user_id: int) -> List[Todo]:
    result = db.query(Todo).filter(Todo.owner == user_id).offset(offset).limit(limit).all()
    return result


def create_todo(db: Session, todo: TodoCreateSchema, user_id: int) -> Todo:
    todo_orm = Todo(**todo.dict(), done=False, owner=user_id)
    if todo_name_exists_for_user(db, todo.name, user_id):
        raise IntegrityError("Todo name exists in the user scope")
    db.add(todo_orm)
    db.commit()
    db.refresh(todo_orm)
    return todo_orm


def get_todo_by_id(db: Session, id: int) -> Todo:
    result = db.query(Todo).filter(Todo.id == id).first()
    return result


def todo_name_exists_for_user(db: Session, name: str, user_id: int) -> bool:
    n = db.query(Todo.name).filter(Todo.name == name, Todo.owner == user_id)\
        .count()
    if n > 0:
        return True
    return False


def get_todo_by_name(db: Session, name: str, user_id: int) -> Todo:
    result = db.query(Todo).filter(Todo.name == name, Todo.owner == user_id).first()
    return result


def update_todo_by_id(db: Session, id: int, update: TodoUpdateSchema) -> Todo:
    todo = db.query(Todo).filter(Todo.id == id).first()
    todo.name = update.name if update.name else todo.name
    todo.description = update.description if update.description else todo.description
    db.commit()
    db.refresh(todo)
    return todo


def delete_todo_by_id(db: Session, id: int) -> int:
    deleted = db.query(Todo).filter(Todo.id == id).delete()
    db.commit()
    return deleted


def get_user_by_username(db: Session, username: str) -> User:
    user = db.query(User).filter(User.name == username).first()
    return user


def get_user_by_id(db: Session, id: int) -> User:
    user = db.query(User).filter(User.id == id).first()
    return user


def insert_user(db: Session, user: UserInsertSchema) -> User:
    user_orm = User(**user.dict())
    user_orm.permissions = [int(i) for i in user.permissions]
    db.add(user_orm)
    db.commit()
    db.refresh(user_orm)
    return user_orm


def refresh_token_used(db: Session, token: str) -> bool:
    amount = db.query(RefreshToken.token).filter(RefreshToken.token == token)\
        .count()

    if amount > 0:
        return True
    return False


def save_refresh_token(db: Session, token: str, user_id: int) -> RefreshToken:
    refresh_token = RefreshToken(
        token=token,
        user_id=user_id,
        active=True,
        token_child=None,
        not_after=datetime.now() + timedelta(days=1)
    )
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    return refresh_token


def get_refresh_token(db: Session, token: str) -> RefreshToken:
    refresh_token = db.query(RefreshToken).filter(RefreshToken.token == token)\
        .first()
    return refresh_token


def add_child_refresh_token(db: Session,
                            token: RefreshToken,
                            child: RefreshToken) -> RefreshToken:
    token.token_child = child.token
    token.active = False
    db.commit()
    db.refresh(token)
    return token


def disable_token(db: Session, token: str) -> RefreshToken:
    token_orm = db.query(RefreshToken).filter(RefreshToken.token == token)\
        .first()
    if not token_orm.active:
        return token_orm
    token_orm.active = False
    db.commit()
    db.refresh(token)
    return token_orm


def deactivate_token_family(db: Session, root_token: RefreshToken) -> int:
    invalidated_count = 0
    while root_token.token_child:
        root_token = disable_token(db, root_token.token_child)
        invalidated_count += 1

    return invalidated_count
