import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.routers import extract_job, analyze_resume
from app.api import jobs
from app.api.resumes import resumes_router, analysis_router, profile_router
from app.config import settings

logger = logging.getLogger("job_track_backend")
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Job Track (JT) AI Intelligence Engine",
    description="Python-first backend service for resume parsing, job extraction, career matching, and job application management",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_msg = str(exc)
    exc_type = type(exc).__name__
    logger.error(f"Unhandled Exception on {request.method} {request.url.path}: [{exc_type}] {error_msg}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {exc_type}", "path": request.url.path}
    )

# Include routers
app.include_router(extract_job.router)
app.include_router(analyze_resume.router)
app.include_router(jobs.router)
app.include_router(resumes_router)
app.include_router(analysis_router)
app.include_router(profile_router)

@app.get("/health")
@app.get("/api/py/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "Job Track FastAPI Primary Backend Engine",
        "gemini_configured": bool(settings.GEMINI_API_KEY)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=settings.PORT, reload=True)

