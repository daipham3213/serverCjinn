import json
import logging
import threading

from django.conf import settings
from django.db import transaction, connection

logger = logging.getLogger(__name__)


# default permission
def create_role_default(org_id, company_id, user_created=None, data_list=None, is_thread=False):
    try:
        with transaction.atomic():
            if data_list is None:
                data_list = settings.ROLE_GROUP_DEFAULT_DATA
            if data_list:
                for role_data in data_list:
                    name, permissions, is_join, is_default, code_system = role_data['name'], role_data['permissions'], role_data['is_join'], role_data['is_default'], role_data['code_system']
                    role = RoleGroup.objects.create(org=org_id, company=company_id, name=role_data['name'], is_default=is_default, code_system=code_system)
                    if role:
                        if user_created and is_join:
                            UserRoleGroup.objects.create(group=role, user_id=user_created)
                        for perm in permissions:
                            codename, option = perm[0], perm[1]
                            permission = Permission.objects.filter(codename=str(codename)).first()
                            if permission:
                                GroupPermission.objects.create(company=company_id, group=role, permission=permission, option=option)
    except Exception as e:
        logger.error(json.dumps({'org': org_id, 'company': company_id, 'user_created': user_created, 'data_list': data_list, 'error': str(e)}))
    if is_thread:
        connection.close()
    threading.Thread(
        target=init_data_workflow,
        args=[org_id, company_id], daemon=True
    ).start()
    return True