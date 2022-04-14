import graphene
from django.utils.translation import gettext_lazy as _

from apps.base.models import Token
from apps.messenger.models import DeviceInfo


class AuthenticationMixin:
    class Arguments:
        registration_id = graphene.Int()
        token = graphene.String()
        thread_id = graphene.UUID()

    @classmethod
    def subscribe(cls, info, *args, **kwargs):
        user, device = None, None
        registration_id = kwargs.get('registration_id', None)
        token = kwargs.get('token', None)
        context = args[0].context
        if hasattr(context, 'user') and hasattr(context, 'device'):
            user = context.user
            device = context.device
        elif registration_id and token:
            user = Token.objects.get(key=token).user
            device = DeviceInfo.objects.get(user=user, registration_id=registration_id)
        if user and device:
            if user.is_authenticated and device:
                kwargs['user'] = user
                kwargs['device'] = device
                return cls.resolve_subscribe(info, *args, **kwargs)
            raise Exception(_('Account activation needed'))
        else:
            raise Exception(_('Invalid credentials'))
