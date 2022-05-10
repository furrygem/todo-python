import datetime
import secrets
import bcrypt
import jwt
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session
from .schemas import TokenPair, UserInsertSchema, UserPermissionsEnum
from .schemas import TokenRefreshRequest
from .models import User
from ..crud import get_user_by_username, insert_user, refresh_token_used
from ..crud import save_refresh_token, get_refresh_token
from ..crud import deactivate_token_family
from ..crud import get_user_by_id, add_child_refresh_token
from . import config


def authenticate_user_password(db: Session,
                               username: str,
                               password: str) -> TokenPair:
    """Authenciate User, return token pair

    Args:
        db (Session):  sqlalchemy session
        username (str): username to authenticate
        password (str): user password
    Returns:
        Token pair(JWT auth token, refresh token)
    """
    user = get_user_by_username(db, username)
    if user:
        if bcrypt.checkpw(password.encode(), user.password.encode()):
            # Password match && user found
            refresh_token = generate_refresh_token()

            while refresh_token_used(db, refresh_token):
                refresh_token = generate_refresh_token()

            save_refresh_token(db, refresh_token, user.id)

            token_pair = TokenPair(
                auth_token=generate_auth_token(user),
                refresh_token=refresh_token
            )
            return token_pair

    raise HTTPException(status_code=403, detail="Wrong username or password")


def register_user(db: Session,
                  username: str,
                  raw_password: str,
                  permissions: list[UserPermissionsEnum]) -> User:
    """Create new user

    Creates new user in the database, hashes the raw_password

    Args:
        db (Session): sqlalchemy session
        username (str): new user's username
        raw_password (str): raw password of the new user

    Returns:
        User: created user
    """
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(raw_password.encode(), salt)
    insert_user_data = UserInsertSchema(
        name=username,
        password=hashed_password.decode(),
        permissions=permissions
    )
    user = insert_user(db, insert_user_data)
    return user


def generate_auth_token(user: User) -> str:
    now = datetime.datetime.now()
    print(f"jwt encode key{ config.jwt_encode_key }")
    token = jwt.encode(
        payload={
            "sub": user.id,
            "name": user.name,
            "iat": now,
            "exp": now + datetime.timedelta(minutes=3),
            "permissions": [int(p) for p in user.permissions],
        }, algorithm=config.jwt_algorithm, key=config.jwt_encode_key
    )

    return token


def generate_refresh_token() -> str:
    token = secrets.token_urlsafe(64)
    return token


def generate_new_token_pair(db: Session, token_refresh_request: TokenRefreshRequest) -> TokenPair:
    """Generate new token pair and invalidate request refresh token

    Generate new auth/refresh tokens pair, and invalidates token specified in
    the request, adds new generated token as it's child. If token was already
    invalidated, invalidate the whole token family. Checks if the token is
    expired


    Args:
        db (Session): sqlalchemy session
        token_refresh_request (TokenRefreshRequest): token refresh request

    Raises:
        HTTPException: Token is not in the database
        HTTPException: Refresh token is invalid, amount of children chain
        HTTPException: Refresh token has expired
        HTTPException: User with user_id not found

    Returns:
        TokenPair: New auth/refresh tokens
    """
    token = get_refresh_token(db, token_refresh_request.refresh_token)
    if not token:
        raise HTTPException(status_code=403,
                            detail="Refresh token can not be accepted")
    if not token.active:
        n = deactivate_token_family(db, token)
        raise HTTPException(status_code=403,
                            detail=f"Refresh token invalid. {n}")
    if token.not_after < datetime.datetime.now():
        raise HTTPException(status_code=403, detail="Refresh token expired")

    user_id = token.user_id
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=403, detail="Token for invalid user")

    auth_token = generate_auth_token(user)
    refresh_token = generate_refresh_token()

    refresh_token_orm = save_refresh_token(db, refresh_token, user.id)
    add_child_refresh_token(db, token, refresh_token_orm)
    return TokenPair(auth_token=auth_token, refresh_token=refresh_token)


def verify_auth_token(request: Request):
    """Checks and verifies application access token

    Args:
        request(Request): requst
    """
    token = request.headers.get('authorization')
    if not token:
        raise HTTPException(status_code=401, detail="No Token")
    stoken = token.split()
    print(stoken)
    print(token)
    try:
        if stoken[0].lower() == "token":
            token_decoded = jwt.decode(
                stoken[1],
                key=config.jwt_decode_key,
                algorithms=config.jwt_accept_algorithms
            )
            return token_decoded
        raise HTTPException(status_code=401, detail="No Token")

    except IndexError:
        raise HTTPException(status_code=401, detail="No Token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token Expired")
    except jwt.DecodeError:
        raise HTTPException(status_code=403, detail="Invalid Token")


def bcrypt_password(password: str) -> str:
    """returns bcrypt hash of specified password

    Args:
        password (str): plaintext password to hash

    Returns:
        str: hash value
    """
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()
