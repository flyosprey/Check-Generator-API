import uvicorn
from fastapi import FastAPI

import models
from database import engine
from routers import auth, check


app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(check.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
