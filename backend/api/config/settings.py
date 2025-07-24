from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "assistant_db"
    LOG_LEVEL: str = "INFO"
    UPLOAD_DIR: str = "uploads"
    
    
    COURSE_COLLECTION: str = "course_vectors"
    COURSE_INDEX:      str = "course_index"


    class Config:
        env_file = ".env"

settings = Settings() 