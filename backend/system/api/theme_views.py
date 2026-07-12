from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsSuperAdmin
from system.models import SystemSetting

THEME_SETTING_KEY = 'ui_theme'
ALLOWED_THEMES = {'classic', 'pulse'}
DEFAULT_THEME = 'classic'


def get_ui_theme() -> str:
    setting = SystemSetting.objects.filter(key=THEME_SETTING_KEY).first()
    if not setting or setting.value not in ALLOWED_THEMES:
        return DEFAULT_THEME
    return setting.value


class UIThemeView(APIView):
    """Platform-wide appearance theme (readable by anyone, writable by super admin)."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def get(self, request):
        return Response({
            'theme': get_ui_theme(),
            'options': [
                {'id': 'classic', 'label': 'Classic', 'description': 'Teal admin theme'},
                {'id': 'pulse', 'label': 'Pulse', 'description': 'Coral accent on light surfaces'},
            ],
        })

    def patch(self, request):
        theme = request.data.get('theme')
        if theme not in ALLOWED_THEMES:
            return Response(
                {'error': f"theme must be one of: {', '.join(sorted(ALLOWED_THEMES))}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        setting, _ = SystemSetting.objects.get_or_create(
            key=THEME_SETTING_KEY,
            defaults={
                'value': DEFAULT_THEME,
                'category': 'general',
                'description': 'Platform UI color theme',
            },
        )
        setting.value = theme
        setting.category = 'general'
        setting.description = 'Platform UI color theme'
        setting.save(update_fields=['value', 'category', 'description', 'updated_at'])

        return Response({'theme': setting.value})
