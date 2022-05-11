from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse


def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": f"{exc.detail}"},
        headers=exc.headers,
    )
