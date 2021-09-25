from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
from django.conf import settings
from django.db import models
from uuid import uuid4
from jsonfield import JSONField


class AuthorizationLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    remarks = models.TextField(verbose_name=_('descriptions'))
    data = JSONField(null=True, blank=True, verbose_name=_('more data'))

    user_created = models.UUIDField(verbose_name=_('user created'), blank=False, null=True, editable=False)
    date_created = models.DateTimeField(verbose_name='date created', default=timezone.now, editable=False)
    date_modified = models.DateTimeField(verbose_name='date modified', auto_now=True)
    is_active = models.BooleanField(verbose_name=_('active'), default=True)
    is_delete = models.BooleanField(verbose_name=_('delete'), default=False)
    in_workflow = models.BooleanField(verbose_name=_('True when it is new document in workflow.'), default=False)
    extras = JSONField(blank=True, null=True, default={})

    class Meta:
        verbose_name = _('Log authorization')
        verbose_name_plural = _('Log authorization')
        ordering = ('-date_created',)
        default_permissions = ()
        permissions = ()


class ActivityLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    remarks = models.TextField(verbose_name=_('descriptions'))
    data = JSONField(null=True, blank=True, verbose_name=_('more data'))
    code_document = models.CharField(max_length=255, null=True, blank=True, verbose_name=_('code feature code'))
    doc_id = models.UUIDField(null=True, verbose_name=_('document activity'))
    doc_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('document name'))
    node_id = models.UUIDField(null=True, verbose_name=_('node id'))
    node_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('node name'))
    node_type = models.SmallIntegerField(choices=settings.ACTIVITY_NODE_TYPE, default=1)  # node_type != 0 <=> != system --> node_id required
    reason = models.TextField(blank=True, null=True, verbose_name=_('reason'))

    user = models.UUIDField(null=True)
    employee = models.UUIDField(null=True)

    user_created = models.UUIDField(verbose_name=_('user created'), blank=False, null=True, editable=False)
    date_created = models.DateTimeField(verbose_name='date created', default=timezone.now, editable=False)
    date_modified = models.DateTimeField(verbose_name='date modified', auto_now=True)
    is_active = models.BooleanField(verbose_name=_('active'), default=True)
    is_delete = models.BooleanField(verbose_name=_('delete'), default=False)
    in_workflow = models.BooleanField(verbose_name=_('True when it is new document in workflow.'), default=False)
    extras = JSONField(blank=True, null=True, default={})

    class Meta:
        verbose_name = _('Log authorization')
        verbose_name_plural = _('Log authorization')
        ordering = ('-date_created',)
        default_permissions = ()
        permissions = ()


class HistoryLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    remarks = models.TextField(blank=True, null=True, verbose_name=_('descriptions'))
    code_document = models.CharField(max_length=255, null=True, blank=True)
    doc_id = models.UUIDField(null=True, verbose_name=_('document history'))
    doc_name = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('document name'))
    doc_detail = JSONField(null=True, verbose_name=_('document detail'))
    doc_new = JSONField(null=True, verbose_name=_('document new detail'))
    doc_change = JSONField(null=True, verbose_name=_('document changed'))
    activity_name = models.CharField(max_length=100, choices=settings.HISTORY_ACTION_NAME, default=0)

    user = models.UUIDField(null=True)
    employee = models.UUIDField(null=True)

    user_created = models.UUIDField(blank=True, null=True, editable=False, verbose_name=_('user created'))
    date_created = models.DateTimeField(default=timezone.now, editable=False, verbose_name=_('date created'))
    is_active = models.BooleanField(default=True, verbose_name=_('active'))
    is_delete = models.BooleanField(default=False, verbose_name=_('deleted'))
    in_workflow = models.BooleanField(default=False, verbose_name=_('in workflow'))
    extras = JSONField(blank=True, null=True)

    class Meta:
        verbose_name = _('History')
        verbose_name_plural = _('History')
        ordering = ('-date_created',)
        default_permissions = ()
        permissions = ()


# Document Log
class DocumentLog(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid4)
    org = models.UUIDField(null=True, verbose_name=_('Organization'))
    company = models.UUIDField(null=True, verbose_name=_('Company'))
    department = models.UUIDField(null=True, verbose_name=_('Company'))

    user_created = models.UUIDField(null=True)
    employee_inherit = models.UUIDField(null=True)
    code_document = models.CharField(max_length=255)
    doc_id = models.UUIDField()
    doc_name = models.CharField(max_length=255, blank=True)
    doc_code = models.CharField(max_length=255, blank=True, null=True)
    doc_status = models.SmallIntegerField(choices=settings.STATUS, help_text=str(settings.STATUS))
    date_created = models.DateTimeField()
    date_modified = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)
    is_delete = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('Document Log')
        verbose_name_plural = _('Document Log')
        ordering = ('-date_created',)
        unique_together = ('org', 'company', 'department', 'doc_id', 'code_document')
        default_permissions = ()
        permissions = ()
