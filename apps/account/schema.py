import channels_graphql_ws
import graphene
from graphene_django.filter import DjangoFilterConnectionField

from .mutations import Register, ObtainOTP, ValidOTP, ResendOTP, ChangePassword
from .types import UserNode


class AccountMutation(graphene.ObjectType):
    register = Register.Field()
    login = ObtainOTP.Field()
    validOTP = ValidOTP.Field()
    resendOTP = ResendOTP.Field()
    changePassword = ChangePassword.Field()


class UserQuery(graphene.ObjectType):
    user = graphene.relay.Node.Field(UserNode)
    users = DjangoFilterConnectionField(UserNode)
    me = graphene.Field(UserNode)

    def resolve_me(self, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None
