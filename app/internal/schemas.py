from enum import IntEnum
from pydantic import BaseModel, Field

# from app.models import Permissions


class TodoSchema(BaseModel):
    id: int
    name: str
    description: str
    owner: int
    done: bool

    class Config:
        orm_mode = True


class TodoCreateSchema(BaseModel):
    name: str
    description: str


class TodoUpdateSchema(BaseModel):
    name: str | None = Field(None)
    description: str | None = Field(None)
    done: bool | None = Field(None)


class UserPermissionsEnum(IntEnum):
    personal_read = 1
    personal_write = 2
    users_listing = 3
    admin = 100


class UserDTOSchema(BaseModel):
    name: str
    raw_password: str

    # permissions: list[UserPermissionsEnum] = [
    #     UserPermissionsEnum.personal_read,
    #     UserPermissionsEnum.personal_write,
    # ]


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


class UserFullSchema(BaseModel):
    id: int
    name: str
    password: str
    permissions: list[UserPermissionsEnum]

    class Config:
        orm_mode = True


class UserDTOSchemaAdmin(UserDTOSchema):
    permissions: list[UserPermissionsEnum]
