from django.contrib import admin
from .models import User, Role, OTPRequest, Session, MFALog

admin.site.register(User)
admin.site.register(Role)
admin.site.register(OTPRequest)
admin.site.register(Session)
admin.site.register(MFALog)