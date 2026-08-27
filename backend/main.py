from fastapi import FastAPI

app = FastAPI(title="Watch2Earn API")


@app.get("/")
def home():
    return {
        "status": "online",
        "app": "Watch2Earn",
        "version": "1.0"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
