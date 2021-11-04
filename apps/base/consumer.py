import channels_graphql_ws
from .schema import schema


class MessengerConsumer(channels_graphql_ws.GraphqlWsConsumer):
    async def on_connect(self, payload):
        print('Hello')


    schema = schema
    middleware = []
