import channels.routing
from channels.auth import AuthMiddlewareStack
from django.conf.urls import url

from apps.base.consumer import MessengerConsumer

websocket_urlpatterns = [
    url(r'^graphql(?:/(?P<token>\w+|))(?:/(?P<device_id>[-\w]+))?/?', MessengerConsumer.as_asgi()),
]

application = channels.routing.ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        channels.routing.URLRouter(
            websocket_urlpatterns
        ))
})
