from enum import IntEnum
from pydantic import BaseModel, Field


class TodoSchema(BaseModel):
    id: int
    name: str
    description: str
    owner: int

    class Config:
        orm_mode = True


class TodoCreateSchema(BaseModel):
    name: str
    description: str


class TodoUpdateSchema(BaseModel):
    name: str | None = Field(None)
    description: str | None = Field(None)


class UserPermissionsEnum(IntEnum):
    personal_read = 1
    personal_write = 2
    users_listing = 3
    admin = 100


class UserDTOSchema(BaseModel):
    name: str
    raw_password: str

    permissions: list[UserPermissionsEnum] = [
        UserPermissionsEnum.personal_read,
        UserPermissionsEnum.personal_write,
    ]


class UserInsertSchema(BaseModel):
    name: str
    password: str
    permissions: list[UserPermissionsEnum]


class UserSchema(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class TokenPair(BaseModel):
    auth_token: str
    refresh_token: str


class TokenRefreshRequest(BaseModel):
    refresh_token: str
