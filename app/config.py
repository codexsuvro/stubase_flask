import os
from dotenv import load_dotenv
from datetime import timedelta

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    R2_ACCOUNT_ID = os.getenv("R2_ACCOUNT_ID")
    R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")
    R2_ACCESS_KEY_ID = os.getenv("R2_ACCESS_KEY_ID")
    R2_SECRET_ACCESS_KEY = os.getenv("R2_SECRET_ACCESS_KEY")
    R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
    R2_SIGNED_URL_TTL_SECONDS = 300
    ASSIGNMENT_PDF_MAX_BYTES = 2 * 1024 * 1024
    MAX_CONTENT_LENGTH = 3 * 1024 * 1024
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = os.getenv("MAIL_PORT", "587")
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true")
    MAIL_FROM_ADDRESS = os.getenv("MAIL_FROM_ADDRESS")
    MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "StuBase")
    
    # ======================
    # JWT Configuration
    # ======================
    JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY")
    OPENAPI_COMPONENTS = {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
    }
    OPENAPI_SWAGGER_UI_CONFIG = {
        "defaultModelsExpandDepth": -1,
    }
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