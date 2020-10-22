def check_permission(permission, user, obj):
    if permission is None:
        return True
    if not user:
        return False
    if callable(permission):
        return permission(user, obj=obj)
    # the ModelBackend returns False as soon as we supply an obj so we can't pass that here
    return user.has_perm(permission)
