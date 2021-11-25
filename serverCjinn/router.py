import channels.routing
from channels.auth import AuthMiddlewareStack
from django.conf.urls import url

from apps.base.consumer import MessengerConsumer
from apps.base.middleware import TokenAuthMiddleware

websocket_urlpatterns = [
    url(r'^graphql(?:/(?P<token>\w+|))(?:/(?P<device_id>[-\w]+))?/?', MessengerConsumer.as_asgi()),
]

application = channels.routing.ProtocolTypeRouter({
    "websocket": TokenAuthMiddleware(AuthMiddlewareStack(
        channels.routing.URLRouter(
            websocket_urlpatterns
        )))
})
