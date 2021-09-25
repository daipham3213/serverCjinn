from django.db import connection

from apps.base.utils import serializer_data
from apps.log.models import AuthorizationLog, ActivityLog, HistoryLog, DocumentLog


def authorization_log(user, remarks, data):
    try:
        AuthorizationLog.objects.create(
            user_created=user,
            remarks=remarks,
            data=data
        )
        return True
    except Exception as e:
        print(e)
    return False


def service_get_author_log(user_id):
    try:
        kwargs = {}
        if user_id:
            kwargs.update({'user_created': user_id})
        auth_logs = AuthorizationLog.objects.filter(**kwargs)
        if auth_logs:
            return serializer_data(auth_logs, ['id', 'date_created', 'date_modified', 'user_created', 'remarks', 'data',
                                               'is_active'])
    except Exception as e:
        print(e)
    return []


def activity_log(user, remarks, doc_id, data, date_created, doc_name='', node_id=None,
                 node_name='', reason='', code_document=None, is_system=True, user_action=None, employee_action=None):
    try:
        ActivityLog.objects.create(
            user_created=user, remarks=remarks, doc_id=doc_id,
            code_document=code_document, data=data, doc_name=doc_name,
            node_id=node_id, node_name=node_name, node_type=0 if is_system else 1, date_created=date_created,
            reason=reason,
            user=user_action, employee=employee_action
        )
        return True
    except Exception as e:
        print(e)
    return False


def service_get_activity_log(user_id):
    try:
        kwargs = {}
        if user_id:
            kwargs.update({'user_created': user_id})
        auth_logs = ActivityLog.objects.filter(**kwargs)
        if auth_logs:
            keys = ['id', 'date_created', 'user_created', 'remarks', 'code_document', 'doc_id', 'doc_name', 'doc_detail', 'doc_new', 'doc_change', 'activity_name', 'is_active']
            return serializer_data(auth_logs, keys)
    except Exception as e:
        print(e)
    return []


def history_log(user, remarks, doc_id, code_document, doc_detail, date_created, activity_name,
                doc_new=None, doc_change=None, user_action=None, employee_action=None):
    try:
        HistoryLog.objects.create(
            remarks=remarks, code_document=code_document,
            doc_id=doc_id, doc_detail=doc_detail, date_created=date_created, activity_name=activity_name,
            user_created=user,
            doc_new=doc_new, doc_change=doc_change,
            user=user_action, employee=employee_action
        )
    except Exception as e:
        print(e)
    return False


def service_sync_document_log(
        user_created, employee_inherit, code_document, doc_id, doc_name, doc_code, doc_status, date_created,
        date_modified,
        is_active, is_delete, is_thread=False, again_num=0
):
    if again_num > 1:
        return False
    else:
        try:
            doc = DocumentLog.objects.filter(doc_id=doc_id,
                                             code_document=code_document).first()
            if doc:
                doc.employee_inherit = employee_inherit
                doc.doc_name = doc_name
                doc.doc_status = doc_status
                doc.date_created = date_created
                doc.date_modified = date_modified
                doc.is_active = is_active
                doc.is_delete = is_delete
                doc.save()
            else:
                doc = DocumentLog.objects.create(
                    user_created=user_created, employee_inherit=employee_inherit, code_document=code_document,
                    doc_id=doc_id, doc_name=doc_name, doc_code=doc_code, doc_status=doc_status,
                    date_created=date_created,
                    date_modified=date_modified,
                    is_active=is_active, is_delete=is_delete
                )
            connection.close() if is_thread else None
            return doc
        except Exception as e:
            print(e)
            return service_sync_document_log(
                user_created, employee_inherit, code_document, doc_id, doc_name, doc_code, doc_status, date_created,
                date_modified,
                is_active, is_delete, is_thread=False, again_num=1
            )
        # return False
