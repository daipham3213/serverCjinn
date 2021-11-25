import channels_graphql_ws

from .middleware import get_user_by_token
from .schema import schema
from ..messenger.func import add_or_update_user_cache, remove_user_cache
from ..messenger.models import DeviceInfo


def demo_middleware(next_middleware, root, info, *args, **kwargs):
    """Demo GraphQL middleware.
    For more information read:
    https://docs.graphene-python.org/en/latest/execution/middleware/#middleware
    """
    # Skip Graphiql introspection requests, there are a lot.
    if (
            info.operation.name is not None
            and info.operation.name.value != "IntrospectionQuery"
    ):
        print("Demo middleware report")
        print("    operation :", info.operation.operation)
        print("    name      :", info.operation.name.value)

    # Invoke next middleware.
    return next_middleware(root, info, *args, **kwargs)


class MessengerConsumer(channels_graphql_ws.GraphqlWsConsumer):

    # send_keepalive_every = 120  # 2 minutes

    # Uncomment to process requests sequentially (useful for tests).
    # strict_ordering = True

    async def on_connect(self, payload):
        try:
            user = self.scope.get('user', None)
            if not user.is_authenticated:
                user = await get_user_by_token(payload.get('authorization', None))
            device_token = payload.get('deviceToken', None)
            if not user or not device_token:
                raise Exception('Invalid credentials')
            if user.is_authenticated:
                self.scope["user"] = user
                device = DeviceInfo.objects.filter(user=user, token=device_token)
                if device.exists():
                    self.scope['device'] = device
                    add_or_update_user_cache(user.id, device.id)
                    await super().on_connect(payload)
        except Exception as e:
            await self.websocket_disconnect(f'Error {e.__str__()}')

    async def disconnect(self, code):
        await super(MessengerConsumer, self).disconnect(code)
        # clean up caches
        user = self.scope.get('user', None)
        device = self.scope.get('device', None)
        if device:
            remove_user_cache(user.id, device.id)
        else:
            remove_user_cache(user.id)

    schema = schema
    middleware = [demo_middleware]
