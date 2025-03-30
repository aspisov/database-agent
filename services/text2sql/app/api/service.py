import uuid

from fastapi import BackgroundTasks, FastAPI, HTTPException

from app.agents.text2sql import create_text2sql_graph
from app.api.models import SQLQueryRequest, SQLQueryResponse

query_store = {}

app = FastAPI(title="Text2SQL Microservice")

text2sql_graph = create_text2sql_graph().compile()


@app.post("/query", response_model=SQLQueryResponse)
async def process_query(request: SQLQueryRequest, background_tasks: BackgroundTasks):
    query_id = str(uuid.uuid4())
    query_store[query_id] = {
        "status": "processing",
        "response": "Your query is being processed",
    }

    background_tasks.add_task(
        process_sql_query, query_id=query_id, user_query=request.user_query
    )
    return SQLQueryResponse(
        query_id=query_id,
        status="processing",
        response="Your query is being processed",
    )


def process_sql_query(query_id: str, user_query: str):
    try:
        response = text2sql_graph.invoke({"user_query": user_query})

        query_store[query_id] = {
            "status": response["status"],
            "response": response["answer"],
        }
    except Exception as e:
        query_store[query_id] = {
            "status": "failed",
            "response": f"Error: {str(e)}",
        }


@app.get("/query/{query_id}", response_model=SQLQueryResponse)
async def get_query_status(query_id: str):
    if query_id not in query_store:
        raise HTTPException(status_code=404, detail="Query not found")

    data = query_store[query_id]
    return SQLQueryResponse(query_id=query_id, **data)
