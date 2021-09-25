# Auth login
LOGIN_URL = '/'
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
LOGIN_VIA_PHONE = False
LOGIN_ATTEMPTS = 10
LOGIN_OTP_LENGTH = 6
LOGIN_OTP_EXPIRE = 15  # minutes
LOGIN_OTP_SEND = False
EXPIRE_VALID_USER = 24  # hours

# Phone
PHONENUMBER_DEFAULT_REGION = 'VN'

# Send Email
SYSTEM_CMIS_ONLINE = 'Cjinn'
EMAIL_ADD_USER_SUBJECT = 'Welcome '
EMAIL_OTP_SUBJECT = '[Cjinn] Ma xac nhan OTP'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'api.projectmng@gmail.com'
EMAIL_HOST_PASSWORD = 'iavzbwnfilltxpqa'
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = 'no-reply@gmail.com'
DEFAULT_SUBJECT = 'Notification'

# allow signup with code
ALLOWED_SIGNUP_CODE = True
