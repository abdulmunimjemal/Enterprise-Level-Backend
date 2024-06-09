from config import get_settings
from app import create_app
from apps import router

app = create_app(router=router, settings=get_settings())

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
