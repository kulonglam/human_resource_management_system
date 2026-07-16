from rest_framework.throttling import AnonRateThrottle, UserRateThrottle, ScopedRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    scope = 'login'


class MFARateThrottle(AnonRateThrottle):
    scope = 'mfa'


class ExportRateThrottle(UserRateThrottle):
    scope = 'export'


class SCIMRateThrottle(UserRateThrottle):
    scope = 'scim'
