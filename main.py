import uvicorn
from fastapi import FastAPI

import models
from controlers import auth, check
from database import engine

app = FastAPI()

models.Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(check.router)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
