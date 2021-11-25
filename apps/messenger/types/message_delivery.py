import graphene

APN_VOIP_NOTIFICATION_PAYLOAD = "{\"aps\":{\"sound\":\"default\",\"alert\":{\"loc-key\":\"APN_Message\"}}}"
APN_NSE_NOTIFICATION_PAYLOAD = "{\"aps\":{\"mutable-content\":1,\"alert\":{\"loc-key\":\"APN_Message\"}}}"
APN_CHALLENGE_PAYLOAD = "{\"aps\":{\"sound\":\"default\",\"alert\":{\"loc-key\":\"APN_Message\"}}, \"challenge\" : \"%s\"}"
APN_RATE_LIMIT_CHALLENGE_PAYLOAD = "{\"aps\":{\"sound\":\"default\",\"alert\":{\"loc-key\":\"APN_Message\"}}, \"rateLimitChallenge\" : \"%s\"}";


class GCMMessage(graphene.ObjectType):
    id = graphene.UUID()
    gcmId = graphene.String(required=True)
    deviceId = graphene.String(required=True)
    type = graphene.Enum('MessageType', [('NOTIFICATION', 0), ('CHALLENGE', 1), ('RATE_LIMIT_CHALLENGE', 2)])
    data = graphene.String()


class APNMessage(graphene.ObjectType):
    id = graphene.UUID()
    apnId = graphene.String(required=True)
    deviceId = graphene.String(required=True)
    isVoid = graphene.Boolean(default_value=False)
    type = graphene.Enum('MessageType', [('NOTIFICATION', 0), ('CHALLENGE', 1), ('RATE_LIMIT_CHALLENGE', 2)])
    challengeData = graphene.String()

    def get_message(self):
        msg_type = self.type if self.type is not None else 0
        if msg_type == 0:
            return APN_VOIP_NOTIFICATION_PAYLOAD if self.isVoid else APN_NSE_NOTIFICATION_PAYLOAD
        if msg_type == 1:
            return APN_CHALLENGE_PAYLOAD.format(s=self.challengeData)
        if msg_type == 2:
            return APN_RATE_LIMIT_CHALLENGE_PAYLOAD.format(s=self.challengeData)


class MessageResponseType(graphene.ObjectType):
    needsSync = graphene.Boolean()


class MultiRecipientResponseType(graphene.ObjectType):
    uuids404 = graphene.List(graphene.UUID)


class FriendOnlineType(graphene.ObjectType):
    user_id = graphene.UUID()
    status = graphene.String()
