from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn
from .langgraph_agent import langgraph

app = FastAPI()

class UserInput(BaseModel):
    query: str
    threshold: float

@app.post("/query")
async def handle_query(user_input: UserInput):
    result = await langgraph.ainvoke({
        "question": user_input.query,
        "passing_threshold": user_input.threshold
    })
    return result

# Optional for local testing
if __name__ == "__main__":
    uvicorn.run("zomato_agent.app:app", host="0.0.0.0", port=8080)