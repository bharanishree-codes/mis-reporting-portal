# your_app/context_processors.py
from user_management.settings_views import get_settings


def settings_processor(request):
    settings = get_settings(request)  # Fetch settings with the request context
    return settings

