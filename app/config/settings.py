import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
    SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID", "")

    GOOGLE_BASE_URL = "https://www.googleapis.com/customsearch/v1"
    USER_AGENT: str = "IdeaHistoryAgent/1.0"

    MAX_GOOGLE_RESULTS: int = 5
    MAX_WIKI_RESULTS: int = 3
    MAX_SNIPPET_LENGTH: int = 200

settings = Settings()
