from django.utils.translation import ugettext_lazy as _

GENDER_CHOICE = (
    ('male', _('Male')),
    ('female', _('Female'))
)

STATUS_DONT_CHANGE = [4, 5, 6]
PERMISSION_ADMIN_FAVOR = (
    {'app_label': 'account', 'model': 'user'},
)
PERMISSION_EVERYBODY_ADD = ()
PERMISSION_ADD_NEED_EMPLOYEE = ()
PERMISSION_CREATED_NO_SHOW = (
    'workflows_workflow', 'workflows_audit', 'workflows_node',
    'employees_employee', 'employees_department', 'employees_department',
    'account_user', 'account_rolegroup',
    'eam_assetgroup'
)
PERMISSION_ADMIN_ADD = ()
PERMISSION_ADMIN_ORG_ADD = ()
PERMISSION_ADMIN_DOC = ()
FILTER_DONT_INHERIT = (
    'account_rolegroup', 'account_user', 'account_company',
    'organizations_organization',
    'employees_employee'
)

PERM_ALL_OPTION = (
    (0, _("Current owner/inherit")),
    (1, _("Current data on system")),
)
