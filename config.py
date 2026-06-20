import os
import logging
from dotenv import load_dotenv

load_dotenv()


class Config:
    APP_NAME = "ResumeRank"
    APP_VERSION = "1.0.0"
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    
    # API Configuration
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", 8000))
    STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", 8501))
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = "logs/app.log"
    
    # Google Generative AI
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY environment variable not set")
    
    # Pinecone Configuration
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "resume-index")
    
    if not PINECONE_API_KEY or not PINECONE_ENVIRONMENT:
        raise ValueError("Pinecone environment variables not set")
    
    # File Upload
    MAX_FILE_SIZE = os.getenv("MAX_FILE_SIZE", "50MB")
    ALLOWED_EXTENSIONS = {"pdf"}
    DATA_DIR = "data/resumes"
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./resume_rag.db")
    
    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "['http://localhost:3000', 'http://localhost:8501']")
    
    # Text Processing
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    # Search
    TOP_K_RESULTS = 5
    SIMILARITY_THRESHOLD = 0.6
    
    @classmethod
    def validate(cls):
        required = ["GOOGLE_API_KEY", "PINECONE_API_KEY", "PINECONE_ENVIRONMENT"]
        missing = [key for key in required if not getattr(cls, key, None)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


class DevelopmentConfig(Config):
    DEBUG_MODE = True
    LOG_LEVEL = "DEBUG"


class ProductionConfig(Config):
    DEBUG_MODE = False
    LOG_LEVEL = "INFO"


class TestingConfig(Config):
    DEBUG_MODE = True
    DATABASE_URL = "sqlite:///./test.db"
    LOG_LEVEL = "DEBUG"


def get_config() -> Config:
    env = os.getenv("ENV", "development").lower()
    
    config_map = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }
    
    config_class = config_map.get(env, DevelopmentConfig)
    config_class.validate()
    return config_class()


def setup_logging(config: Config) -> logging.Logger:
    os.makedirs(os.path.dirname(config.LOG_FILE) or ".", exist_ok=True)
    
    logger = logging.getLogger("resume_rag")
    logger.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # File handler
    file_handler = logging.FileHandler(config.LOG_FILE)
    file_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, config.LOG_LEVEL))
    
    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Get config and setup logging
config = get_config()
logger = setup_logging(config)
