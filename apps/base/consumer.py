from re import sub

import channels_graphql_ws
from asgiref.sync import sync_to_async
from channels_graphql_ws.scope_as_context import ScopeAsContext

from apps.messenger.models.credentials import UserInfo

from .middleware import get_user_by_token
from .schema import schema
from ..messenger.func import add_or_update_user_cache, remove_user_cache
from ..messenger.models import DeviceInfo
from ..messenger.subscriptions import FriendOnlineSubscription


class MessengerConsumer(channels_graphql_ws.GraphqlWsConsumer):
    # send_keepalive_every = 120  # 2 minutes

    # Uncomment to process requests sequentially (useful for tests).
    strict_ordering = True

    async def on_connect(self, payload):
        try:
            context = ScopeAsContext(self.scope)
            user = context.user
            if not user.is_authenticated:
                token = payload.get('authorization', '')
                token = sub('Bearer ', '', token)
                user = await get_user_by_token(token)
            device_token = payload.get('deviceToken', None)
            if not user or not device_token:
                raise Exception('Invalid credentials')
            if user.is_authenticated:
                device_token = sub('Bearer ', '', device_token)
                device = await self.find_device(user.id, device_token)
                context.user = user
                context.device = device
                print(device.id, "Connected")
                await super().on_connect(payload)
        except Exception as e:
            await self.websocket_disconnect(f'Error {e.__str__()}')

    async def disconnect(self, *arg, **kwargs):
        await super().disconnect(*arg, **kwargs)
        # clean up caches
        user = self.scope.get('user', None)
        device = self.scope.get('device', None)
        if device:
            await self.device_fetches_messages(device, False)
            remove_user_cache(user.id, device.id)
        else:
            remove_user_cache(user.id)
        if user and device:
            await self.send_online_notify(user, device, False)

    schema = schema

    @sync_to_async
    def find_device(self, user_id, device_token):
        try:
            return DeviceInfo.objects.filter(user_id=user_id, token=device_token).first()
        except DeviceInfo.DoesNotExist:
            raise Exception('Invalid credentials')
        
    @sync_to_async
    def device_fetches_messages(self, device, state=True):
        device.fetches_messages = state
        device.save()

    @sync_to_async
    def send_online_notify(self, user, device, is_connect=True):
        add_or_update_user_cache(user.id, device.id)
        FriendOnlineSubscription.send_notify(user_id=user.id, device_id=device.id, is_connect=is_connect)
