import graphene

from apps.base.converter import AutoCamelCasedScalar

from apps.account.mixins import AuthRegisterMixin, AuthOTPValidMixin, AuthOTPResendMixin, AuthLoginMixin, \
    ChangePasswordMixin, ResetPasswordMixin
from apps.base.mixins import MutationMixin, DynamicArgsMixin
from apps.base.utils import normalize_fields


class Register(MutationMixin, DynamicArgsMixin, AuthRegisterMixin, graphene.Mutation):
    __doc__ = AuthRegisterMixin.__doc__

    result = AutoCamelCasedScalar()

    _required_args = normalize_fields(['username', 'email', 'first_name', 'last_name'], [])


class ValidOTP(MutationMixin, DynamicArgsMixin, AuthOTPValidMixin, graphene.Mutation):
    __doc__ = AuthOTPValidMixin.__doc__

    result = AutoCamelCasedScalar()

    _args = ['pk', 'otp']


class ResendOTP(MutationMixin, DynamicArgsMixin, AuthOTPResendMixin, graphene.Mutation):
    __doc__ = AuthOTPResendMixin.__doc__

    result = AutoCamelCasedScalar()

    _required_args = ['pk']


class ObtainOTP(MutationMixin, DynamicArgsMixin, AuthLoginMixin, graphene.Mutation):
    __doc__ = AuthLoginMixin.__doc__

    result = AutoCamelCasedScalar()

    _required_args = ['username', 'password']


class ChangePassword(MutationMixin, DynamicArgsMixin, ChangePasswordMixin, graphene.Mutation):
    __doc__ = ChangePasswordMixin.__doc__

    result = AutoCamelCasedScalar()

    _required_args = ['password_old', 'password_new']


class ResetPassword(MutationMixin, DynamicArgsMixin, ResetPasswordMixin, graphene.Mutation):
    __doc__ = ResetPasswordMixin.__doc__

    result = AutoCamelCasedScalar()

    _required_args = ['username']


