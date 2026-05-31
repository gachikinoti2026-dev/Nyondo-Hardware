from django.contrib.auth.decorators import user_passes_test


def admin_required(view_func):
    return user_passes_test(
        lambda u: u.is_superuser or u.groups.filter(name='admin').exists()
    )(view_func)


def sales_attendant_required(view_func):
    return user_passes_test(
        lambda u: u.groups.filter(name='sales_attendant').exists()
    )(view_func)


def store_manager_required(view_func):
    return user_passes_test(
        lambda u: u.groups.filter(name='store_manager').exists()
    )(view_func)