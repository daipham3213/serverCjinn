from uuid import UUID
from datetime import datetime, date

from graphene import String
from graphene_django.converter import convert_django_field
from jsonfield import JSONField

from graphene.types.generic import GenericScalar
from graphene.utils.str_converters import to_camel_case, to_snake_case


def FieldsPatches(auto_camel_scalar=True):
    @convert_django_field.register(JSONField)
    def convert_JSONField_to_GenericScalar(field, registry=None):
        scalar = AutoCamelCasedScalar if auto_camel_scalar else GenericScalar
        return scalar(description=field.help_text, required=not field.null)

    @convert_django_field.register(datetime)
    def convert_datetime_to_string(field, registry=None):
        return String()

    @convert_django_field.register(date)
    def convert_date_to_string(field, registry=None):
        return String()

    @convert_django_field.register(UUID)
    def convert_uuid_to_string(field, registry=None):
        return String()

    @convert_django_field.register(bytes)
    def convert_bytes_to_string(field, registry=None):
        return String()


class AutoCamelCasedScalar(GenericScalar):
    """
    JSON as is, but converting object keys to and from camelCase automatically
    """

    @classmethod
    def serialize(cls, value):
        value = super().serialize(value)
        return convert_keys(value, to_camel_case)

    @classmethod
    def parse_literal(cls, node):
        node = super().parse_literal(node)
        return convert_keys(node, to_snake_case)

    @classmethod
    def parse_value(cls, value):
        value = super().parse_value(value)
        return convert_keys(value, to_snake_case)


def convert_keys(data, to):
    """
    Convert object keys either to camelCase or to snake_case
    @param data: object - processed recursively
    @param to: callable - applied to each key of each object found
    """
    if isinstance(data, dict):
        return {to(key): convert_keys(value, to) for key, value in data.items()}

    if isinstance(data, (list, tuple)):
        return [convert_keys(value.decode("utf-8"), to) for value in data]

    if isinstance(data, (datetime, date)):
        return data.strftime('%Y-%m-%dT%H:%M:%SZ')
    elif isinstance(data, UUID):
        return data.__str__()
    elif isinstance(data, bytes):
        return data.__str__()
    return data
