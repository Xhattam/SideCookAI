from asgiref.wsgi import WsgiToAsgi
from main import app

wsgi_app = WsgiToAsgi(app)
