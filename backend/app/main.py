from fastapi import FastAPI

app = FastAPI(title="RevPilot API")

@app.get("/")
def read_root():
    return {
        "project": "RevPilot",
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }
