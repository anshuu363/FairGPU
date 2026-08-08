from fastapi import FastAPI

app = FastAPI(title="FairGPU Scheduler")

@app.get("/")
async def root():
    return {"message": "FairGPU Scheduler is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}