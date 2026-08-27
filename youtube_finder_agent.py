import os
import sys
import yt_dlp
from google import genai

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
            # ytsearch<N>:query
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

def main():
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Please set it before running the script: set GEMINI_API_KEY=your_key")
        sys.exit(1)
        
    client = genai.Client()
    
    print("==============================================")
    print("Welcome to the Agentic YouTube Video Finder!")
    print("==============================================")
    print("Ask the agent to find videos on any topic (or type 'quit' to exit).\n")
    
    previous_interaction_id = None
    
    sys_instruct = (
        "You are a helpful, knowledgeable AI assistant that helps users find and curate YouTube videos. "
        "Use the 'search_youtube' tool to find relevant videos based on the user's prompt. "
        "Present the search results in a friendly, engaging markdown format. Always include the video "
        "title, the channel, the number of views, and the direct URL link."
    )
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit']:
                print("Goodbye!")
                break
            
            if not user_input.strip():
                continue
                
            print("Agent is thinking and searching...")
            
            interaction = client.interactions.create(
                model="gemini-3.7-flash",
                input=user_input,
                tools=[search_youtube],
                system_instruction=sys_instruct,
                previous_interaction_id=previous_interaction_id
            )
            
            previous_interaction_id = interaction.id
            print("\nAgent:\n" + ("-" * 40))
            print(interaction.output_text)
            print("-" * 40 + "\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}\n")

if __name__ == "__main__":
    main()
