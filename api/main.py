"""
FastAPI application entrypoint for Simulation Lab.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import time
import uuid

from mathematical_engine.core.errors import SimulationLabError
from api.routes.health import router as health_router
from api.routes.connectors import router as connectors_router
from api.routes.discovery import router as discovery_router
from api.routes.ontology import router as ontology_router
from api.routes.dag import router as dag_router
from api.routes.scenarios import router as scenarios_router
from api.routes.simulations import router as simulations_router
from api.routes.optimization import router as optimization_router
from api.routes.explainability import router as explainability_router
from api.routes.chat import router as chat_router

app = FastAPI(
    title="Simulation Lab API",
    description="Universal, Ontology-Driven, Explainable Simulation and Optimization Platform",
    version="0.1.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request timing and Request-ID middleware
@app.middleware("http")
async def add_process_time_and_request_id(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = (time.time() - start_time) * 1000.0
    response.headers["X-Request-ID"] = req_id
    response.headers["X-Response-Time-Ms"] = f"{process_time:.2f}"
    return response


# Simulation Lab error handling
@app.exception_handler(SimulationLabError)
async def simulation_lab_exception_handler(request: Request, exc: SimulationLabError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error_type": exc.__class__.__name__,
            "message": str(exc),
            "path": request.url.path,
        },
    )


# Register all API routers
app.include_router(health_router)
app.include_router(connectors_router)
app.include_router(discovery_router)
app.include_router(ontology_router)
app.include_router(dag_router)
app.include_router(scenarios_router)
app.include_router(simulations_router)
app.include_router(optimization_router)
app.include_router(explainability_router)
app.include_router(chat_router)


@app.get("/")
def root():
    return {
        "platform": "Simulation Lab",
        "status": "operational",
        "docs_url": "/docs",
    }
