import graphene
from graphene_django.filter import DjangoFilterConnectionField

from .models import User
from .mutations import Register, ObtainOTP, ValidOTP, ResendOTP, ChangePassword
from .types import UserNode, UserInfoType


class AccountMutation(graphene.ObjectType):
    register = Register.Field()
    login = ObtainOTP.Field()
    validOTP = ValidOTP.Field()
    resendOTP = ResendOTP.Field()
    changePassword = ChangePassword.Field()


class UserQuery(graphene.ObjectType):
    user_info = graphene.Field(UserInfoType, id=graphene.UUID(required=True))
    find_user = DjangoFilterConnectionField(UserNode)
    me = graphene.Field(UserNode)

    @staticmethod
    def resolve_me(root, info, **kwargs):
        user = info.context.user
        if user.is_authenticated:
            return user
        return None

    @staticmethod
    def resolve_user(root, info, **kwargs):
        if hasattr(info.context, 'user') and info.context.user.is_authenticated:
            return User.objects.get(id=kwargs.get('id', None))

    @staticmethod
    def resolve_user_info(root, info, **kwargs):
        return User.objects.get(id=kwargs.get('id', None))
