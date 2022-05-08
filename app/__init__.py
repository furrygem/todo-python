import fastapi
from app.config import Config


api = fastapi.FastAPI()
api.__setattr__('config', Config("config.yaml").config)

print(api.config.jwt_encode_key_file)
# api = fastapi.APIRouter(prefix="/api")
