# user_management/templatetags/customtags.py
from django import template

register = template.Library()


@register.simple_tag
def get_request_path(request):
    path_val = request.path
    prefix_val = path_val.replace("/home_page/","")[:-1]
    request.path = prefix_val
    return request.path
