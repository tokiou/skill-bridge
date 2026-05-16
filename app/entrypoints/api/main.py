from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

api_router = APIRouter(prefix="/api")



def main_router(app: FastAPI):
    app.include_router(api_router)



main_router(app)