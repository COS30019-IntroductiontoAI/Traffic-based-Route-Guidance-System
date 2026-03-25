from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(
    title="Route Guidance System API",
    description="API for fetching optimal traffic routes based on machine learning predictions.",
    version="1.0.0"
)

# CORS Middleware to allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class RouteRequest(BaseModel):
    origin: str
    destination: str
    topK: int = 5
    algorithm: str = "xgboost"
    year: str = "2014"

class RouteSegment(BaseModel):
    from_node: str
    to_node: str
    time: float
    traffic: str

class RouteResult(BaseModel):
    nodes: List[str]
    time: float
    distance: float
    segments: List[RouteSegment]

@app.get("/")
def read_root():
    return {"message": "Welcome to the Route Guidance Traffic System API. Use /docs to test with Swagger or use Postman."}

@app.post("/api/routes", response_model=List[RouteResult])
def get_routes(req: RouteRequest):
    """
    Get top-k optimal routes based on ML predictions.
    This endpoint currently returns placeholder logic but can be tested via Postman.
    Load your dataset and models here when ready.
    """
    
    if int(req.year) not in [2006, 2014]:
        raise HTTPException(status_code=400, detail="Year must be 2006 or 2014")

    # Mock response to verify Postman functionality
    mock_routes = []
    for i in range(req.topK):
        base_time = 15.0 + i * 2.5
        
        # Simulate difference based on year
        if req.year == "2014":
            base_time *= 1.15
            traffic_status = "heavy" if i == 0 else "moderate"
        else:
            base_time *= 0.9
            traffic_status = "moderate" if i == 0 else "clear"

        mock_routes.append(RouteResult(
            nodes=[req.origin, "node_mid_1", "node_mid_2", req.destination],
            time=round(base_time, 1),
            distance=round(5.0 + i * 0.5, 1),
            segments=[
                RouteSegment(from_node=req.origin, to_node="node_mid_1", time=round(base_time/3, 1), traffic=traffic_status),
                RouteSegment(from_node="node_mid_1", to_node="node_mid_2", time=round(base_time/3, 1), traffic=traffic_status),
                RouteSegment(from_node="node_mid_2", to_node=req.destination, time=round(base_time/3, 1), traffic=traffic_status)
            ]
        ))
        
    return mock_routes

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
