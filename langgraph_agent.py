import asyncio
import os
import sys
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

async def main():
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable not set.")
        print("Please set it before running the script: set GEMINI_API_KEY=your_key")
        sys.exit(1)

    # Initialize the LLM (using the latest stable model as recommended, or gemini-1.5-pro for langchain defaults if 3.7 isn't mapped yet, but let's try gemini-2.5-flash or gemini-3.7-flash, langchain might use gemini-pro)
    # We will use "gemini-3.7-flash" if possible. Let's use it.
    llm = ChatGoogleGenerativeAI(model="gemini-3.7-flash")

    # Define server connection parameters for the MCP server
    # We run the youtube_mcp_server.py script via the python executable
    server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "youtube_mcp_server.py")
    server_params = StdioServerParameters(
        command=sys.executable,
        args=[server_path],
    )

    print("==============================================")
    print("Welcome to the LangGraph YouTube Finder!")
    print("Connecting to the MCP Server...")
    
    # Connect and load tools from the MCP server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Convert MCP tools to LangChain tools
            tools = await load_mcp_tools(session)
            
            if not tools:
                print("Failed to load tools from MCP server.")
                return
            
            print(f"Loaded {len(tools)} tools from MCP server.")
            print("==============================================\n")
            
            # Create a LangGraph React agent using the LLM and the tools
            system_prompt = (
                "You are a helpful, knowledgeable AI assistant that helps users find and curate YouTube videos. "
                "Use the provided tools to find relevant videos based on the user's prompt. "
                "Present the search results in a friendly, engaging markdown format. Always include the video "
                "title, the channel, the number of views, and the direct URL link."
            )
            agent = create_react_agent(llm, tools, state_modifier=system_prompt)
            
            print("Chat with the agent (type 'quit' to exit).")
            
            while True:
                try:
                    user_input = input("\nYou: ")
                    if user_input.lower() in ['quit', 'exit']:
                        print("Goodbye!")
                        break
                    
                    if not user_input.strip():
                        continue
                        
                    print("Agent is thinking and searching...")
                    
                    # We maintain conversation history by running it through the graph.
                    # Since it's a simple loop, we will just send the single message here.
                    # A more robust implementation would pass a thread_id config for state persistence.
                    response = await agent.ainvoke(
                        {"messages": [HumanMessage(content=user_input)]},
                        config={"configurable": {"thread_id": "1"}}
                    )
                    
                    print("\nAgent:\n" + ("-" * 40))
                    # The last message in the response is the agent's final answer
                    print(response["messages"][-1].content)
                    print("-" * 40 + "\n")
                    
                except KeyboardInterrupt:
                    print("\nGoodbye!")
                    break
                except Exception as e:
                    print(f"\nAn error occurred: {e}\n")

if __name__ == "__main__":
    asyncio.run(main())
