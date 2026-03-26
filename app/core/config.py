from pydantic_settings import BaseSettings
from typing import Literal

class Settings(BaseSettings):
    app_name: str = "Recipe RAG Service"
    host: str = "0.0.0.0"
    port: int = 8000

    # data_path: str = "./data/C8/cook"
    data_path: str = "D:/all-in-rag-app/app/data/C8/cook"
    index_save_path: str = "D:/all-in-rag-app/vector_index"

    embedding_model: str = "BAAI/bge-small-zh-v1.5"
    llm_provider: Literal["moonshot", "deepseek", "openai"] = "deepseek"
    llm_model: str = "deepseek-chat"
    temperature: float = 0.1
    max_tokens: int = 2048
    top_k: int = 3

    history_window: int = 6
    memory_top_k: int = 3
    reflection_window: int = 3

    sqlite_path: str = "D:/all-in-rag-app/app.db"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()