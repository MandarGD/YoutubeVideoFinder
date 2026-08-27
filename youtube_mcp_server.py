import yt_dlp
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server
mcp = FastMCP("YouTube Search Server")

@mcp.tool()
def search_youtube(topic: str, max_results: int = 5) -> str:
    """
    Searches YouTube for a specific topic and returns video details.
    
    Args:
        topic: The topic or query to search for on YouTube.
        max_results: The maximum number of videos to return.
    """
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'dump_single_json': True,
        'default_search': 'ytsearch',
        'noplaylist': True,
        'simulate': True
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            search_query = f"ytsearch{max_results}:{topic}"
            result = ydl.extract_info(search_query, download=False)
            
            if 'entries' in result:
                entries = result['entries']
                videos = []
                for entry in entries:
                    title = entry.get('title', 'No Title')
                    url = entry.get('url', 'No URL')
                    view_count = entry.get('view_count', 'Unknown')
                    channel = entry.get('uploader', 'Unknown Channel')
                    
                    videos.append(
                        f"Title: {title}\n"
                        f"Channel: {channel}\n"
                        f"Views: {view_count}\n"
                        f"URL: {url}\n"
                    )
                return "\n".join(videos)
            else:
                return "No videos found."
    except Exception as e:
        return f"Error searching YouTube: {str(e)}"

if __name__ == "__main__":
    # Run the MCP server over stdio transport
    mcp.run(transport="stdio")
