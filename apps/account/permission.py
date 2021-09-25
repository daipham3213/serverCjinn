from django.contrib.auth.models import Permission
from django.db.models import Q

from apps.account.models import UserPermission, GroupPermission, UserRoleGroup
from apps.account.utils import format_codename_to_all
from apps.base.middleware import get_user_extra
from serverCjinn import settings


