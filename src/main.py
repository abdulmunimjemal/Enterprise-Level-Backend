from core.config import get_settings
from app import create_app
from apps import router

app = create_app(router=router, settings=get_settings())
