from fastapi import FastAPI

from marketiq.api.routes_rest import router


def create_app() -> FastAPI:

    app = FastAPI()

    app.include_router(router)
    return app
