from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

from apps.account.models import RoleGroup, UserRoleGroup, UserPermission, GroupPermission
from django.db import connection


def service_get_user_detail(user_id, is_list=False, is_check=False):
    if is_list:
        try:
            if user_id:
                result_list = []
                user_list = get_user_model().objects.filter(id__in=user_id)
                for user in user_list:
                    detail = {
                        'id': user.id, 'first_name': user.first_name, 'last_name': user.last_name, 'email': user.email,
                        'phone': str(user.phone), 'dob': user.dob, 'gender': user.gender,
                        'language': user.language, 'avatar': user.avatar, 'is_email': user.is_email,
                        'is_phone': user.is_phone, 'date_joined': user.date_joined, 'is_active': user.is_active
                    }
                    if not detail['avatar']:
                        detail.update({'avatar': None})
                    result_list.append(detail)
                return result_list
            return []
        except Exception as e:
            print(e)
        return []
    else:
        try:
            if user_id:
                user = get_user_model().objects.get(pk=user_id)
                detail = {
                    'id': user.id, 'first_name': user.first_name, 'last_name': user.last_name, 'email': user.email,
                    'phone': str(user.phone), 'dob': user.dob, 'gender': user.gender,
                    'language': user.language, 'avatar': user.avatar, 'is_email': user.is_email,
                    'is_phone': user.is_phone, 'date_joined': user.date_joined, 'is_active': user.is_active
                }
                if not detail['avatar']:
                    detail.update({'avatar': None})
                return detail
            return {}
        except Exception as e:
            print(e)
        return {}


def service_get_role_group_detail(group_id, is_detail=False, is_list=False, is_check=False):
    if is_list:
        try:
            list_group = RoleGroup.objects.filter(id__in=group_id)
            if is_detail:
                return [{
                    "id": x.id,
                    "name": x.name,
                    "user": [{
                        "id": user_group.user.id,
                        "first_name": user_group.user.first_name,
                        "last_name": user_group.user.last_name,
                        "email": user_group.user.email,
                        "phone": user_group.user.phone
                    } for user_group in UserRoleGroup.objects.select_related('user').filter(group=x)]
                } for x in list_group]
            else:
                return [{
                    "id": x.id,
                    "name": x.name
                } for x in list_group]
        except Exception as e:
            print(e)
            return []
    else:
        try:
            group = RoleGroup.objects.get(pk=group_id)
            if is_detail:
                list_user_of_group = UserRoleGroup.objects.select_related('user').filter(group=group)
                return {
                    "id": group.id,
                    "name": group.name,
                    "user": [{
                        "id": x.id,
                        "first_name": x.first_name,
                        "last_name": x.last_name,
                        "email": x.email,
                        "phone": x.phone
                    } for x in list_user_of_group]
                }
            else:
                return {
                    "id": group.id,
                    "name": group.name
                }
        except Exception as e:
            print(e)
            return {}


def service_assign_perm(user_id_list, permission_code, doc_id_list):
    try:
        permission = Permission.objects.get(codename=permission_code)
        user_list = [get_user_model().objects.get(pk=user) for user in user_id_list]
        for doc_id in doc_id_list:
            for user in user_list:
                doc_type = '_'.join(permission_code.split('_')[-2:])
                user_perm = UserPermission.objects.create(user=user, permission=permission, doc_id=doc_id,
                                                          doc_type=doc_type)
        return True
    except Exception as e:
        print(e)
    return False


def service_get_role_default(org_id, company_id, code_system):
    role = RoleGroup.objects.filter(org=org_id, company=company_id, is_default=True, code_system=code_system).first()
    if role:
        return {"id": role.id, "name": role.name}
    return {}


def service_handle_perm_apply_for(ref_id, ref_type, perm_add, perm_remove, is_thread=False):
    """
        org_id: - UUID4
            ID của organization
        company_id: - UUID4
            ID của company.
        ref_id : - UUID4
            ID của apply for (ID của employee/department/...)
        ref_type :  - Character 100
            ('user', _('user')),
            ('department', _('Department')),
            ('job_position', _('Job Position')),
            ('position_type', _('Position Type'))
        perm_data_add: - List
            [
                {
                    'codename': 'view_all_account_user', # code name của quyền hệ thống
                    'doc_type': 'wbs_project',  # doc_type của doc_id (crm_workspace/wbs_project)
                    'doc_id': 'uuid4'   # id của workspace/project.
                } #
            ]
        perm_remove: - List
            [
                {
                    'codename': 'view_all_account_user',
                    'doc_type': 'crm_workspace',
                    'doc_id': 'uuid4'
                }
            ]


        ex:
        (
        "6a4202b9-4bdc-4ae6-bfb7-4343ea5e4b62", "f7e0ebeb-c267-4bad-b68c-451b9335de45", "a157cb72-d1d4-412d-b382-a2c82c1b06bc", "department",
        perm_add=[{"codename": "view_all_quotation_quotation", "doc_type": "crm_workspace", "doc_id": "ada68a74-8b07-49f6-9088-832fc7a0a632"}],
        perm_remove=[{"codename": "delete_all_quotation_quotation", "doc_type": "wbs_project", "doc_id": "eeafe5f6-1e51-4a76-9b52-7c424a7d5cdf"}]
        )
        với:
        6a4202b9-4bdc-4ae6-bfb7-4343ea5e4b62 : organization ID
        f7e0ebeb-c267-4bad-b68c-451b9335de45 : company ID
        a157cb72-d1d4-412d-b382-a2c82c1b06bc : department ID
        department                           : department
        [{"codename": "view_all_quotation_quotation", "doc_type": "crm_workspace", "doc_id": "ada68a74-8b07-49f6-9088-832fc7a0a632"}] :
            view_all_quotation_quotation            : code name quyền
            crm_workspace                           : doc_type của phiếu workspace/project
            ada68a74-8b07-49f6-9088-832fc7a0a632    : doc_id của phiếu workspace/project
    """
    success = RolePermHandleApplyFor(ref_id=ref_id, ref_type=ref_type, perm_data_add=perm_add,
                                     perm_data_remove=perm_remove).handle()
    connection.close() if is_thread else None
    return success


class RolePermHandleApplyFor:
    perm_data_list = []
    role = None

    def __init__(self, perm_data_add, perm_data_remove, ref_id, ref_type):
        self.perm_data_add = perm_data_add
        self.perm_data_remove = perm_data_remove
        self.ref_id = ref_id
        self.ref_type = ref_type
        if not isinstance(self.perm_data_add, list):
            self.perm_data_add = []
        if not isinstance(self.perm_data_remove, list):
            self.perm_data_remove = []

        role = RoleGroup.objects.filter(is_hidden=True, ref_id=ref_id, ref_type=ref_type).first()
        if not role:
            role_name = '{} {}'.format(str(ref_type), ' system')
            role = RoleGroup.objects.create(name=role_name, is_hidden=True, ref_id=ref_id, ref_type=ref_type)
        self.role = role

    @classmethod
    def convert_data(cls, perm_data):
        kwargs = {}
        if 'option' in perm_data:
            kwargs.update({'option': perm_data['option']})
        if 'more' in perm_data:
            kwargs.update({'more': perm_data['more']})
        if 'lower_level' in perm_data:
            kwargs.update({'lower_level': perm_data['lower_level']})
        if 'doc_type' in perm_data:
            kwargs.update({'doc_type': perm_data['doc_type']})
        if 'doc_id' in perm_data:
            kwargs.update({'doc_id': perm_data['doc_id']})

        # del key
        for key in ['option', 'more', 'lower_level']:
            if key in kwargs:
                del kwargs[key]
        return kwargs

    def handle(self):
        if self.role:
            # add
            for perm_data in self.perm_data_add:
                try:
                    permission = Permission.objects.filter(codename=perm_data['codename']).first()
                    if permission:
                        kw_data = self.convert_data(perm_data)
                        role_perm = GroupPermission.objects.filter(group_id=self.role.id, permission_id=permission.id, **kw_data).first()
                        if role_perm:
                            for key in ['doc_type', 'doc_id']:
                                if key in perm_data:
                                    setattr(role_perm, key, perm_data[key])
                            role_perm.save()
                        else:
                            GroupPermission.objects.create(group_id=self.role.id, permission_id=permission.id, **kw_data)
                    else:
                        print('perm error ', perm_data)
                except Exception as e:
                    print(e)

            # remove
            for perm_data in self.perm_data_remove:
                try:
                    permission = Permission.objects.filter(codename=perm_data['codename']).first()
                    if permission:
                        kw_data = self.convert_data(perm_data)
                        role_perm = GroupPermission.objects.filter(group_id=self.role.id, permission_id=permission.id, **kw_data).first()
                        if role_perm:
                            role_perm.delete()
                        else:
                            print('role not found: ', perm_data)
                    else:
                        print('perm error ', perm_data)
                except Exception as e:
                    print(e)
            return True
        elif self.ref_type == 'user':
            user_obj = get_user_model().objects.filter(id=self.ref_id).first()
            if user_obj:
                for perm_data in self.perm_data_add:
                    try:
                        permission = Permission.objects.filter(codename=perm_data['codename']).first()
                        if permission:
                            kw_data = self.convert_data(perm_data)
                            role_perm = UserPermission.objects.filter(user_id=user_obj.id, permission_id=permission.id, **kw_data).first()
                            if role_perm:
                                for key in ['doc_type', 'doc_id']:
                                    if key in perm_data:
                                        setattr(role_perm, key, perm_data[key])
                                role_perm.save()
                            else:
                                UserPermission.objects.create(user_id=user_obj.id, permission_id=permission.id, **kw_data)
                        else:
                            print('perm error ', perm_data)
                    except Exception as e:
                        print(e)

                # remove
                for perm_data in self.perm_data_remove:
                    try:
                        permission = Permission.objects.filter(codename=perm_data['codename']).first()
                        if permission:
                            kw_data = self.convert_data(perm_data)
                            role_perm = UserPermission.objects.filter(user_id=user_obj.id, permission_id=permission.id, **kw_data).first()
                            if role_perm:
                                role_perm.delete()
                            else:
                                print('role not found: ', perm_data)
                        else:
                            print('perm error ', perm_data)
                    except Exception as e:
                        print(e)
                return True
        return False
