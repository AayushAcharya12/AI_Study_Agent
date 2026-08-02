from langchain_core.tools import tool
from googleapiclient.discovery import build
from src.config import youtube_api
from src.models import youtube

@tool
def youtube_search_tool(query: str):
    """
    Search YouTube for relevant educational videos.
        Search YouTube for relevant educational videos.

    Use this tool when the user wants video tutorials,
    lectures, demonstrations, or visual explanations.

    Args:
        query: Topic or concept to search for.

    Returns:
        List of relevant YouTube videos with title,
        channel name, and URL.

    """
    try:
        response = youtube.search().list(part="snippet",q=query,maxResults=5,type="video",videoCategoryId="27").execute()

        videos = []
        for item in response["items"]:
            video_id = item["id"]["videoId"]
            thumbnails = item["snippet"]["thumbnails"]
            thumbnail_url = (thumbnails.get("medium", {}).get("url") or thumbnails.get("default", {}).get("url"))

            videos.append({"title": item["snippet"]["title"],"channel": item["snippet"]["channelTitle"],"url": f"https://www.youtube.com/watch?v={video_id}","thumbnail": thumbnail_url,}
            ) 
        return videos

    except Exception as e:
        return {"error": f"YouTube search failed: {str(e)}"}