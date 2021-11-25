from django.utils.translation import ugettext_lazy as _

ACTIVITY_NODE_TYPE = (
    (0, _('System')),
    (1, _('Workflow'))
)
HISTORY_ACTION_NAME = (
    ('system', _('System')),
    ('save', _('Save')),
    ('edit', _('Edit')),
    ('delete', _('Delete')),
    ('cancel', _('Cancel')),
    ('comment', _('Comment')),
    ('share', _('Share'))
)

DOCS_CODE = (
    ('key_bundle_update', _('update key bundle'))
)