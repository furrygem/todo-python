import enum
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime
from app.db import Base


class Todo(Base):
    __tablename__ = 'todos'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)


class Permissions(enum.Enum):
    """User permissions
    admin:
        - List users
        - update other users todos
        - reset passwords
        - permissions altering
    """
    personal_read = 1
    personal_write = 2
    users_listing = 3
    admin = 100


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True)
    password = Column(String)

    _permissions = Column('permissions', String)

    def get_permissions(self):
        return self._permissions.split(',')

    def set_permissions(self, permissions: list[int]):
        self._permissions = ','.join([str(i) for i in permissions])

    permissions = property(get_permissions, set_permissions, doc="permissions")


class RefreshToken(Base):
    __tablename__ = 'refresh_tokens'

    token = Column(Text, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    token_child = Column(Text, ForeignKey('refresh_tokens.token'))
    not_after = Column(DateTime)
    active = Column(Boolean)
