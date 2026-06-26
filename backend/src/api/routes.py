from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from main import run_agentic_workflow, run_health_checks
from src.auth.security import check_query_validity

router = APIRouter()


# 1. Define Request/Response schemas
class QuestionRequest(BaseModel):
    query: str


class AnswerResponse(BaseModel):
    query: str
    answer: str


# 2. Define Endpoints
@router.get("/health")
def health_check():
    """Returns the health status of external services."""
    status = run_health_checks()
    return {"services": status}


@router.post("/ask", response_model=AnswerResponse)
async def ask_agent(request: QuestionRequest):
   
    try:
        check_query_validity(request.query)
        # We use the common workflow defined in main.py
        answer = run_agentic_workflow(request.query)
        return AnswerResponse(query=request.query, answer=answer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
