from core.config import get_settings
from app import create_app
from apps import router
from mangum import Mangum

app = create_app(router=router, settings=get_settings())
handler = Mangum(app)
