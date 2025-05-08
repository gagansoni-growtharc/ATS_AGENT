from pathlib import Path
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
import os
from functools import lru_cache

class Settings(BaseSettings):
    """Configuration settings for the ATS Filtering System."""
    
    # MongoDB connection
    MONGO_URI: str = Field(
        default="mongodb://localhost:27017/",
        description="MongoDB connection URI"
    )
    
    # Output directories
    OUTPUT_DIR: Path = Field(
        default=Path("filtered_resumes"),
        description="Directory for filtered resumes"
    )
    
    # Knowledge base settings
    KB_DIR: Path = Field(
        default=Path("knowledge_base"),
        description="Directory for knowledge base documents"
    )
    
    # Model settings
    OPENAI_API_KEY: str = Field(
        default="",
        description="OpenAI API key"
    )
    
    # PgVector settings
    PG_CONNECTION_STRING: str = Field(
        default="",
        description="PostgreSQL connection string for vector database"
    )
    
    @field_validator("OUTPUT_DIR", "KB_DIR", mode="after")
    @classmethod
    def validate_directories(cls, v: Path) -> Path:
        """Validate and resolve directory paths."""
        # Convert Windows backslash paths correctly
        if isinstance(v, str):
            v = Path(v.replace('\\', '/'))
        
        # Ensure path is absolute
        if not v.is_absolute():
            v = Path.cwd() / v
            
        # Create directory if it doesn't exist
        os.makedirs(v, exist_ok=True)
            
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
@lru_cache()
def get_settings() -> Settings:
    """Get settings instance (cached)."""
    return Settings()