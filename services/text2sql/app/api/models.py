from pydantic import BaseModel


class SQLQueryRequest(BaseModel):
    user_query: str


class SQLQueryResponse(BaseModel):
    query_id: str
    status: str
    response: str
