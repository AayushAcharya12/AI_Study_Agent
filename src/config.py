import os
from dotenv import load_dotenv


load_dotenv()

# Calling our API keys
tavily_api = os.getenv("TAVILY_API")
youtube_api = os.getenv("YOUTUBE_API")
google_api = os.getenv("GOOGLE_API")
groq_api = os.getenv("GROQ_API")

try:
    if not tavily_api:
        raise ValueError("TAVILY_API is missing. Please add it to your .env file.")

    if not youtube_api:
        raise ValueError("YOUTUBE_API is missing. Please add it to your .env file.")

    if not google_api:
        raise ValueError("GOOGLE_API is missing. Please add it to your .env file.")

    if not groq_api:
        raise ValueError("GROQ_API is missing. Please add it to your .env file.")

except Exception as e:
    raise Exception(f"Error loading API Keys: {e}") from e