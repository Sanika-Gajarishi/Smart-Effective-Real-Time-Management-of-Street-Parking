import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.layers import get_channel_layer
from parking_app.consumers import ParkingNotificationConsumer
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ParkingSystem.settings')

django_asgi_app = get_asgi_application()

websocket_urlpatterns = [
    path('ws/parking/', ParkingNotificationConsumer.as_asgi()),
]

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
