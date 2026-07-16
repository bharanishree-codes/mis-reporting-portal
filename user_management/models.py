from django.contrib.auth.models import User
from django.db import models


# Create your models here.

class SettingsModel(models.Model):
    application_name = models.CharField(max_length=200)
    api_url = models.CharField(max_length=200)
    favicon_caption = models.CharField(max_length=200)
    favicon_logo = models.ImageField(upload_to='images/')

    def __str__(self):
        return self.application_name


class MenusDetailsModel(models.Model):
    MENU_CHOICES = [
        ('models', 'Models'),
        ('sqlviews', 'Sql Views'),
        ('auth', 'Authentication'),
        ('customapi', 'Custom API'),
        ('coreapi', 'Core API'),
        ('cmspage', 'Cms Page'),
    ]

    STARTER_CHOICES = [
        ('user_master', 'User Master'),
        ('roles_master', 'Roles Master'),
        ('user_privilege', 'User Privilege'),
        ('menu_elements', 'Menu Elements'),
        ('menu_privilege', 'Menu Privilege'),
    ]

    uid = models.CharField(max_length=200)
    table_name = models.CharField(max_length=200)
    menu_type = models.CharField(max_length=200, choices=MENU_CHOICES)
    authentication_key_value = models.CharField(max_length=200)
    starter_menu = models.CharField(max_length=200, null=True, blank=True, choices=STARTER_CHOICES)
    api_method = models.CharField(max_length=200)
    doc_url = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        return self.uid


class StudioMenus(models.Model):
    menu_name = models.CharField(max_length=200, null=True, blank=True)
    menu_uid = models.CharField(max_length=200, unique=False)
    menu_href = models.CharField(max_length=200, null=True, blank=True)
    menu_ui_code = models.CharField(max_length=200, null=True, blank=True)
    icon_class = models.CharField(max_length=100, null=True, blank=True)
    active = models.BooleanField(default=True)
    menu_app_bar = models.CharField(max_length=200, null=True, blank=True)
    menu_order = models.IntegerField(null=True, blank=True)
    menu_code = models.CharField(max_length=200, null=True, blank=True)
    menu_type = models.CharField(max_length=200, null=True, blank=True)
    menu_parent_id = models.IntegerField(null=True, blank=True)
    psk_id = models.IntegerField(null=True, blank=True)

    def __int__(self):
        return self.psk_id


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    studio_menus = models.ManyToManyField(StudioMenus, blank=True)

    def __str__(self):
        return self.user.username
