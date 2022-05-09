from sqlite3 import IntegrityError
import sqlalchemy.exc
from sqlalchemy.orm import Session
from fastapi import Depends, Response, HTTPException, Request
from fastapi.responses import JSONResponse
from app import api
from app.auth import authenticate_user_password, verify_auth_token
from app.auth import generate_new_token_pair
from app.auth import register_user
from app.schemas import TodoSchema, TodoCreateSchema, TodoUpdateSchema, UserPermissionsEnum
from app.schemas import UserSchema
from app.schemas import UserDTOSchema, TokenPair, TokenRefreshRequest
from app.db import SessionLocal, Base, engine
from app import crud


Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@api.exception_handler(HTTPException)
def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": f"{exc.detail}"},
        headers=exc.headers,
    )


@api.get('/api/todos', response_model=list[TodoSchema])
def get_todos_list(offset: int = 0,
                   limit: int = 100,
                   db: Session = Depends(get_db),
                   token: dict[str, any] = Depends(verify_auth_token)):

    print(f"getting for user {token['sub']}")
    permissions: list[str] = token['permissions']
    if UserPermissionsEnum.personal_read not in permissions:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = crud.get_todos_for_user(db, offset, limit, token['sub'])
    return result


@api.post('/api/todos', response_model=TodoSchema, status_code=201)
def create_todo(todo: TodoCreateSchema,
                response: Response,
                db: Session = Depends(get_db),
                token: dict[str, any] = Depends(verify_auth_token)):
    permissions = token['permission']
    if UserPermissionsEnum.personal_write not in permissions:
        raise HTTPException(status_code=403, detail="Not authorized")
    try:
        result = crud.create_todo(db, todo, token['sub'])
    except IntegrityError:
        raise HTTPException(status_code=400, detail=f"Todo Name Exists in the user scope")
    resource_url = api.url_path_for('get_todo_by_id', todo_id=result.id)
    response.headers['Location'] = resource_url
    return result


@api.get('/api/todos/{todo_id}', response_model=TodoSchema)
def get_todo_by_id(todo_id: int,
                   db: Session = Depends(get_db),
                   token: dict[str, any] = Depends(verify_auth_token)):
    permissions = token['permissions']
    if UserPermissionsEnum.personal_read not in permissions:
        raise HTTPException(status_code=403, detail="Not authorized")
    result = crud.get_todo_by_id(db, todo_id)
    return result


@api.put('/api/todos/{todo_id}', response_model=TodoSchema)
def update_todo_by_id(todo_id: int,
                      update: TodoUpdateSchema,
                      db: Session = Depends(get_db),
                      token: dict[str, any] = Depends(verify_auth_token)):
    permissions = token['permissions']
    if UserPermissionsEnum.personal_read not in permissions or\
       UserPermissionsEnum.personal_write not in permissions:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = crud.update_todo_by_id(db, todo_id, update)
    print(result.name, result.description)
    return result


@api.delete('/api/todos/{todo_id}')
def delete_todo_by_id(
    todo_id: int,
    response: Response,
    db: Session = Depends(get_db),
):
    # TODO check user write permissions
    permissions = token['permissions']
    if UserPermissionsEnum.personal_read not in permissions or\
       UserPermissionsEnum.personal_write not in permissions:
        raise HTTPException(status_code=403, detail="Not authorized")
    if crud.delete_todo_by_id(db, todo_id) == 0:
        raise HTTPException(404, 'Not Found')

    response.status_code = 200
    return


@api.post('/api/auth/login', response_model=TokenPair)
def login(user: UserDTOSchema, db: Session = Depends(get_db)):
    token_pair = authenticate_user_password(db, user.name, user.raw_password)
    return token_pair


@api.post('/api/auth/register', response_model=UserSchema)
def register(user: UserDTOSchema, db: Session = Depends(get_db)):
    try:
        user = register_user(
            db,
            user.name,
            user.raw_password,
            permissions=user.permissions
        )

    except sqlalchemy.exc.IntegrityError:
        raise HTTPException(status_code=400, detail="Username already in use")
    return user


@api.post('/api/auth/refresh_token', response_model=TokenPair)
def refresh_token(token_refresh_request: TokenRefreshRequest,
                  db: Session = Depends(get_db)):
    token_pair = generate_new_token_pair(db, token_refresh_request)
    return token_pair


@api.get('/secret')
def secret(token: dict[str, any] = Depends(verify_auth_token)):
    return token.get('name')
