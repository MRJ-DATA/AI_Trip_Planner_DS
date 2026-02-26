from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage

from agent.agentic_workflow import GraphBuilder

app = FastAPI()


# Match Streamlit payload
class QueryRequest(BaseModel):
    question: str


@app.post("/query")
async def query_travel_agent(request: QueryRequest):
    try:
        # Build graph once per request (OK for now)
        graph_builder = GraphBuilder(model_provider="groq")
        app_graph = graph_builder()

        # Prepare messages for LangGraph
        messages = {
            "messages": [HumanMessage(content=request.question)]
        }

        # Invoke graph
        output = app_graph.invoke(messages)

        # Extract LLM response
        final_answer = ""
        best_itinerary = None
        satisfaction_score = None

        if isinstance(output, dict):
            if "messages" in output:
                final_answer = output["messages"][-1].content

            # DS outputs (if present)
            best_itinerary = output.get("best_itinerary")
            satisfaction_score = output.get("satisfaction_score")

        return {
            "answer": final_answer,
            "best_itinerary": best_itinerary,
            "satisfaction_score": satisfaction_score
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )