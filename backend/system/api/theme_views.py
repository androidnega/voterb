from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsSuperAdmin
from system.models import SystemSetting

THEME_SETTING_KEY = 'ui_theme'
DASHBOARD_SETTING_KEY = 'ui_dashboard'
ALLOWED_THEMES = {'classic', 'pulse'}
ALLOWED_DASHBOARDS = {'atelier', 'operations'}
DEFAULT_THEME = 'classic'
DEFAULT_DASHBOARD = 'atelier'

THEME_OPTIONS = [
    {'id': 'classic', 'label': 'Classic', 'description': 'Sage soft-UI palette for the admin shell'},
    {'id': 'pulse', 'label': 'Pulse', 'description': 'Coral accent on light surfaces'},
]

DASHBOARD_OPTIONS = [
    {
        'id': 'atelier',
        'label': 'Atelier Soft',
        'description': 'Card mosaic with turnout gauge, sparklines, and activity — the current admin dashboard.',
    },
    {
        'id': 'operations',
        'label': 'Operations',
        'description': 'Compact stats, charts, and quick-access links for dense election ops.',
    },
]


def get_ui_theme() -> str:
    setting = SystemSetting.objects.filter(key=THEME_SETTING_KEY).first()
    if not setting or setting.value not in ALLOWED_THEMES:
        return DEFAULT_THEME
    return setting.value


def get_ui_dashboard() -> str:
    setting = SystemSetting.objects.filter(key=DASHBOARD_SETTING_KEY).first()
    if not setting or setting.value not in ALLOWED_DASHBOARDS:
        return DEFAULT_DASHBOARD
    return setting.value


def upsert_setting(key: str, value: str, description: str):
    setting, _ = SystemSetting.objects.get_or_create(
        key=key,
        defaults={
            'value': value,
            'category': 'general',
            'description': description,
        },
    )
    setting.value = value
    setting.category = 'general'
    setting.description = description
    setting.save(update_fields=['value', 'category', 'description', 'updated_at'])
    return setting


class UIThemeView(APIView):
    """Platform-wide appearance theme and admin dashboard template."""

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def get(self, request):
        return Response({
            'theme': get_ui_theme(),
            'dashboard': get_ui_dashboard(),
            'options': THEME_OPTIONS,
            'dashboard_options': DASHBOARD_OPTIONS,
        })

    def patch(self, request):
        theme = request.data.get('theme')
        dashboard = request.data.get('dashboard')

        if theme is not None and theme not in ALLOWED_THEMES:
            return Response(
                {'error': f"theme must be one of: {', '.join(sorted(ALLOWED_THEMES))}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if dashboard is not None and dashboard not in ALLOWED_DASHBOARDS:
            return Response(
                {'error': f"dashboard must be one of: {', '.join(sorted(ALLOWED_DASHBOARDS))}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if theme is None and dashboard is None:
            return Response(
                {'error': 'Provide theme and/or dashboard'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if theme is not None:
            upsert_setting(THEME_SETTING_KEY, theme, 'Platform UI color theme')
        if dashboard is not None:
            upsert_setting(DASHBOARD_SETTING_KEY, dashboard, 'Admin dashboard layout template')

        return Response({
            'theme': get_ui_theme(),
            'dashboard': get_ui_dashboard(),
        })
