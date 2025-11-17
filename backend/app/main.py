from fastapi import FastAPI

app = FastAPI()

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Welcome to my project!",
        "version": "0.1.0",
        "docs": "/docs",
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": "dev",
        "version": "0.1.0",
    }
