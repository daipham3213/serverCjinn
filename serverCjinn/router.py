import channels.routing
from channels.auth import AuthMiddlewareStack
from django.conf.urls import url

from apps.base.consumer import MessengerConsumer

websocket_urlpatterns = [
    url("ws/graphql", MessengerConsumer.as_asgi()),
]

application = channels.routing.ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(channels.routing.URLRouter(
        websocket_urlpatterns
    ))
})
