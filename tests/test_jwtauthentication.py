from app.auth import JWTAuthentication


def test_init():
    JWTAuthentication("HS256", "key")