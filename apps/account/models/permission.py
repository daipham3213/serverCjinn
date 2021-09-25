from uuid import uuid4

from django.conf import settings
from django.db.models import Manager
from django.contrib.auth.models import Permission
from django.db import models
from jsonfield import JSONField

from .user import RoleGroup, User


class GroupPermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    group = models.ForeignKey(RoleGroup, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    option = models.SmallIntegerField(choices=settings.PERM_ALL_OPTION, default=0)
    more = JSONField(default=[])
    lower_level = models.BooleanField(default=False)
    doc_type = models.CharField(max_length=100, blank=False, null=True, editable=False)
    doc_id = models.UUIDField(blank=False, null=True, editable=False)
    by_pass_wbs = models.BooleanField(default=False)
    extras = JSONField(blank=True, null=True, default={})

    objects = Manager()

    class Meta:
        default_permissions = ()
        permissions = ()


class UserPermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)
    option = models.SmallIntegerField(choices=settings.PERM_ALL_OPTION, default=0)
    more = JSONField(default=[])
    lower_level = models.BooleanField(default=False)
    doc_type = models.CharField(max_length=100, blank=False, null=True, editable=False)
    doc_id = models.UUIDField(blank=False, null=True, editable=False)
    by_pass_wbs = models.BooleanField(default=False)
    extras = JSONField(blank=True, null=True, default={})

    class Meta:
        default_permissions = ()
        permissions = ()
