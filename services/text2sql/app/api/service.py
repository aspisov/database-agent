import uuid
from typing import Any, Dict, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel

from app.agents.text2sql import create_text2sql_subgraph
from app.database.connector import DatabaseConnector


class SQLQueryRequest(BaseModel):
    query: str
    db_connection_string: Optional[str] = None
    db_schema: Optional[str] = None


class SQLQueryResponse(BaseModel):
    query_id: str
    status: str
    message: str
    sql_query: Optional[str] = None
    execution_results: Optional[Dict[str, Any]] = None


query_store = {}

app = FastAPI(title="Text2SQL Microservice")

text2sql_graph = create_text2sql_subgraph().compile()


@app.post("/query", response_model=SQLQueryResponse)
async def process_query(request: SQLQueryRequest, background_tasks: BackgroundTasks):
    query_id = str(uuid.uuid4())
    query_store[query_id] = {
        "status": "processing",
        "message": "Query is being processed",
    }

    background_tasks.add_task(
        process_sql_query, query_id=query_id, query_text=request.query
    )
    return SQLQueryResponse(
        query_id=query_id,
        status="processing",
        message="Your query is being processed",
    )


def process_sql_query(query_id: str, query_text: str):
    try:
        db = DatabaseConnector()
        result = text2sql_graph.invoke({"user_query": query_text, "connector": db})

        execution_results = db.execute_query(result["sql_query"])
        print(db.to_dataframe(execution_results))
        query_store[query_id] = {
            "status": "completed",
            "message": "Query processed successfully",
            "sql_query": result["sql_query"],
            "execution_results": execution_results,
        }
    except Exception as e:
        query_store[query_id] = {
            "status": "failed",
            "message": f"Error: {str(e)}",
        }


@app.get("/query/{query_id}", response_model=SQLQueryResponse)
async def get_query_status(query_id: str):
    if query_id not in query_store:
        raise HTTPException(status_code=404, detail="Query not found")

    data = query_store[query_id]
    return SQLQueryResponse(query_id=query_id, **data)
