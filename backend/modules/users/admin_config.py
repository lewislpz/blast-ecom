from django.contrib.admin.apps import AdminConfig


class BlastEcomAdminConfig(AdminConfig):
    default_site = "modules.users.admin_site.BlastEcomAdminSite"
