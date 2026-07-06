import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # ======================
    # JWT Configuration
    # ======================
    JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES=timedelta(minutes=30)
    JWT_REFRESH_TOKEN_EXPIRES=timedelta(days=7)
    JWT_TOKEN_LOCATION=["headers"]
    JWT_HEADER_NAME="Authorization"
    JWT_HEADER_TYPE="Bearer"
    
    # ==================================
    # Swagger / OpenAPI configuration
    # ==================================
    API_TITLE = "StuBase Management API"
    API_VERSION = "v1"
    OPENAPI_VERSION = "3.0.3"
    OPENAPI_URL_PREFIX = "/"
    OPENAPI_SWAGGER_UI_PATH = "/swagger-ui"
    OPENAPI_SWAGGER_UI_URL = "https://cdn.jsdelivr.net/npm/swagger-ui-dist/"