import graphene


class AddFriendRequestType(graphene.ObjectType):
    to = graphene.String()
