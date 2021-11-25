class Message:
    INVALID_PRE_KEY_BUNDLE = [{'message': 'Invalid pre-key bundle', 'code': 'invalid_pre_key_bundle'}]
    INVALID_CREDENTIAL = [{'message': 'Invalid credential provided', 'code': 'invalid_credential'}]
    PRE_KEY_COUNT_EXCEEDED = [{'message': 'Pre-key count exceed', 'code': 'pre_key_count_exceeded'}]
    INVALID_SIGNED_PRE_KEY = [{'message': 'Invalid signed pre key format', 'code': 'invalid_signed_pre_key'}]
    DEVICE_LIMIT_EXCEED = [{'message': 'Maximum device limit exceeded', 'code': 'maximum_device_exceed'}]
    DEVICE_VERIFICATION_CODE_SEND = [
        {'message': 'Device verification code sent successfully', 'code': 'device_verification_code_sent'}]
    NO_AUTH_DEVICE = [{'message': 'No authenticated device', 'code': 'invalid_auth_device'}]
    INVALID_DATA_FORMAT = [{'message': 'Invalid data format. Please check your params', 'code': 'invalid_format'}]


# temporary
FRIEND_ONLINE = 'friend_online'
INCOMING_MGS = 'incoming_message'
FRIEND_REQUEST = 'friend_request'
