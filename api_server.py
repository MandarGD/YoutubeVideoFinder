import os
import sys
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Global variables to store the initialized agent
app_state = {
    "agent": None,
    "mcp_context": None
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize before the server starts accepting requests
    if not os.environ.get("GEMINI_API_KEY"):
        print("WARNING: GEMINI_API_KEY environment variable not set.")
    
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-3.7-flash")
        
        server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "youtube_mcp_server.py")
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_path],
        )
        
        # Start the MCP Client subprocess
        cm = stdio_client(server_params)
        read, write = await cm.__aenter__()
        
        session = ClientSession(read, write)
        await session.initialize()
        
        tools = await load_mcp_tools(session)
        
        system_prompt = (
            "You are a helpful, knowledgeable AI assistant that helps users find and curate YouTube videos. "
            "Use the provided tools to find relevant videos based on the user's prompt. "
            "Present the search results in a friendly, engaging markdown format. Always include the video "
            "title, the channel, the number of views, and the direct URL link."
        )
        
        agent = create_agent(llm, tools, system_prompt=system_prompt)
        
        app_state["agent"] = agent
        app_state["mcp_context"] = (cm, session)
        
        print(f"Server initialized successfully. Loaded {len(tools)} MCP tools.")
        yield
    except Exception as e:
        print(f"Failed to initialize server: {e}")
        yield
    finally:
        # Cleanup when shutting down
        if app_state["mcp_context"]:
            cm, _ = app_state["mcp_context"]
            await cm.__aexit__(None, None, None)

app = FastAPI(lifespan=lifespan)

# Allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    reply: str

@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    agent = app_state.get("agent")
    if not agent:
        raise HTTPException(status_code=500, detail="Agent is not initialized. Check server logs.")
        
    try:
        response = await agent.ainvoke(
            {"messages": [HumanMessage(content=request.message)]},
            config={"configurable": {"thread_id": "api-thread"}}
        )
        reply_content = response["messages"][-1].content
        return ChatResponse(reply=reply_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_server:app", host="127.0.0.1", port=8000, reload=True)
