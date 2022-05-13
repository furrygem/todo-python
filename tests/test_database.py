import pytest
from sqlite3 import IntegrityError

from app.internal.config import Config
from app.crud import create_todo, delete_todo_by_id, get_todo_by_name, get_todos, update_todo_by_id
from app.crud import get_todos_for_user, insert_user, get_user_by_username
from app.internal.schemas import TodoCreateSchema, UserInsertSchema
from app.internal.schemas import UserPermissionsEnum, TodoUpdateSchema
from app.internal.db import engine, Base, SessionLocal
from app.internal.auth import bcrypt_password


TEST_TODO = TodoCreateSchema(
    name='test',
    description='test',
)


def setup():
    Config("test-config.yaml")


class TestTodos:
    def setup_class(cls):
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            user = UserInsertSchema(
                name='test',
                password=bcrypt_password('test'),
                permissions=[UserPermissionsEnum.personal_read,
                             UserPermissionsEnum.personal_write],
            )
            user = insert_user(db, user)
            cls._base_user = user

    def teardown_class(cls):
        Base.metadata.drop_all(bind=engine)

    def test_create_todo(cls):
        with SessionLocal() as db:
            todo = TodoCreateSchema(
                name='test',
                description='test',
            )
            user_id = get_user_by_username(db, 'test').id
            create_todo(db, todo, user_id)  # type: ignore

    def test_create_todo_existing_name(cls):
        with SessionLocal() as db:
            user_id = cls._base_user.id
            todo = get_todo_by_name(db, 'test', user_id)  # type: ignore
            if not todo:
                cls.test_create_todo()

            # if it does create new one with the same name for the same user
            new_todo = TodoCreateSchema(
                name='test',
                description='exists',
            )
            with pytest.raises(IntegrityError,
                               match="^Todo name exists in the user scope$"):
                create_todo(db, new_todo, user_id)  # type: ignore

            # else create test and create the new one for the same user

    def test_get_todos(cls):
        with SessionLocal() as db:
            todos = get_todos(db, offset=0, limit=100)
            assert todos[0].name == 'test'

    def test_get_todos_for_user(cls):
        with SessionLocal() as db:
            user_id = cls._base_user.id
            todos = get_todos_for_user(db,
                                       offset=0,
                                       limit=100,
                                       user_id=user_id)  # type: ignore

            assert todos[0].name == 'test'

            todos = get_todos_for_user(db, offset=0, limit=100, user_id=0)
            assert len(todos) == 0

    def test_get_todo_by_name(cls):
        with SessionLocal() as db:
            user_id = cls._base_user.id
            todo = get_todo_by_name(db, 'test', user_id)  # type: ignore
            assert todo.id > 0
            assert todo.name == "test"

    def test_update_todo_by_id(cls):
        with SessionLocal() as db:
            #  Create todo
            todo = TodoCreateSchema(
                name='test_update',
                description='test_update',
            )
            user_id = cls._base_user.id
            assert user_id
            todo = create_todo(db, todo, user_id)  # type: ignore

            # check todo.done == false
            assert not todo.done

            # set todo.done to true
            update = TodoUpdateSchema(done=True)  # type: ignore
            todo = update_todo_by_id(db, todo.id, update)  # type: ignore

            # check todo.done == true
            assert todo.done

    def test_delete_todo_by_id(cls):
        with SessionLocal() as db:
            user_id = cls._base_user.id
            todo = get_todo_by_name(db, 'test', user_id)  # type: ignore
            assert todo

            deleted = delete_todo_by_id(db, todo.id)  # type: ignore
            assert deleted == 1

            todo = get_todo_by_name(db, 'test', user_id)  # type: ignore
            assert not todo
