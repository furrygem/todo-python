import bcrypt
import pytest
from sqlite3 import IntegrityError

from app.internal.config import Config
from app.crud import create_todo, delete_todo_by_id, delete_user, get_todo_by_name, list_users, update_user
from app.crud import get_todos_for_user, insert_user, get_user_by_username
from app.crud import get_todos, update_todo_by_id, get_user_by_id
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
    def setup_class(self):
        Base.metadata.create_all(bind=engine)
        with SessionLocal() as db:
            user = UserInsertSchema(
                name='test',
                password=bcrypt_password('test'),
                permissions=[UserPermissionsEnum.personal_read,
                             UserPermissionsEnum.personal_write],
            )
            user = insert_user(db, user)
            self._base_user = user

    def teardown_class(self):
        Base.metadata.drop_all(bind=engine)

    def test_create_todo(self):
        with SessionLocal() as db:
            todo = TodoCreateSchema(
                name='test',
                description='test',
            )
            user_id = get_user_by_username(db, 'test').id
            create_todo(db, todo, user_id)  # type: ignore

    def test_create_todo_existing_name(self):
        with SessionLocal() as db:
            user_id = self._base_user.id
            todo = get_todo_by_name(db, 'test', user_id)  # type: ignore
            if not todo:
                self.test_create_todo()

            # if it does create new one with the same name for the same user
            new_todo = TodoCreateSchema(
                name='test',
                description='exists',
            )
            with pytest.raises(IntegrityError,
                               match="^Todo name exists in the user scope$"):
                create_todo(db, new_todo, user_id)  # type: ignore

            # else create test and create the new one for the same user

    def test_get_todos(self):
        with SessionLocal() as db:
            todos = get_todos(db, offset=0, limit=100)
            assert todos[0].name == 'test'

    def test_get_todos_for_user(self):
        with SessionLocal() as db:
            user_id = self._base_user.id
            todos = get_todos_for_user(db,
                                       offset=0,
                                       limit=100,
                                       user_id=user_id)  # type: ignore

            assert todos[0].name == 'test'

            todos = get_todos_for_user(db, offset=0, limit=100, user_id=0)
            assert len(todos) == 0

    def test_get_todo_by_name(self):
        with SessionLocal() as db:
            user_id = self._base_user.id
            todo = get_todo_by_name(db, 'test', user_id)  # type: ignore
            assert todo.id > 0
            assert todo.name == "test"

    def test_update_todo_by_id(self):
        with SessionLocal() as db:
            #  Create todo
            todo = TodoCreateSchema(
                name='test_update',
                description='test_update',
            )
            user_id = self._base_user.id
            assert user_id
            todo = create_todo(db, todo, user_id)  # type: ignore

            # check todo.done == false
            assert not todo.done

            # set todo.done to true
            update = TodoUpdateSchema(done=True)  # type: ignore
            todo = update_todo_by_id(db, todo.id, update)  # type: ignore

            # check todo.done == true
            assert todo.done

    def test_delete_todo_by_id(self):
        with SessionLocal() as db:
            user_id = self._base_user.id
            todo = get_todo_by_name(db, 'test', user_id)  # type: ignore
            assert todo

            deleted = delete_todo_by_id(db, todo.id)  # type: ignore
            assert deleted == 1

            todo = get_todo_by_name(db, 'test', user_id)  # type: ignore
            assert not todo


class TestUsers:
    def setup_class(self):
        Base.metadata.create_all(bind=engine)

    def teardown_class(self):
        Base.metadata.drop_all(bind=engine)

    def test_insert_user(self):
        with SessionLocal() as db:
            user_is = UserInsertSchema(
                name='test',
                password=bcrypt_password('test'),
                permissions=[
                    UserPermissionsEnum.personal_read,
                    UserPermissionsEnum.personal_write,
                ]
            )
            user = insert_user(db, user_is)
        assert user
        assert user.name == 'test'
        assert bcrypt.checkpw(b'test', user.password.encode())

    def test_get_user_by_username(self):
        with SessionLocal() as db:
            user = get_user_by_username(db, 'test')
        assert user
        assert user.name == 'test'

    def test_get_user_by_id(self):
        with SessionLocal() as db:
            print("aaaaa 2")
            uid = get_user_by_username(db, 'test').id
            user = get_user_by_id(db, uid)  # type: ignore
        assert user
        assert user.name == 'test'
        assert bcrypt.checkpw(b'test', user.password.encode())

    def test_list_users(self):
        with SessionLocal() as db:
            users = list_users(db, 0, 100)
        assert len(users) == 1

    def test_update_user(self):
        with SessionLocal() as db:
            user = get_user_by_username(db, 'test')
            update = UserInsertSchema(
                name='updated',
                permissions=user.permissions,
                password=user.password,  # type: ignore
            )
            user = update_user(db, user.id, update)  # type: ignore
        assert user.name == 'updated'

    def test_delete_user(self):
        with SessionLocal() as db:
            user = get_user_by_username(db, 'updated')
            deleted = delete_user(db, user.id)  # type: ignore
            user = get_user_by_username(db, 'updated')

        assert deleted == 1
        assert not user
