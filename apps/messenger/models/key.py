from uuid import uuid4

from django.db import models
from django.utils.translation import ugettext_lazy as _


class PreKey(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    publicKey = models.TextField(verbose_name=_('public key'))

    class Meta:
        verbose_name = _('Preparation Key')
        verbose_name_plural = _('Preparation Keys')
        default_permissions = ()


class SignedPreKey(PreKey):
    signature = models.TextField(verbose_name=_('pre-key signature'))

    class Meta:
        verbose_name = _('Signed pre-key')
        verbose_name_plural = _('Signed pre-keys')
        default_permissions = ()
