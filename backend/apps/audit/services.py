from apps.audit.models import AuditEvent


def emit(*, merchant_id=None, actor_user=None, actor=None, entity, entity_id, action, old_value=None, new_value=None):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    user = actor_user if actor_user is not None else actor
    user_obj = None
    user_id = None
    if user is not None:
        if isinstance(user, int):
            user_id = user
        elif isinstance(user, User):
            user_obj = user
        elif hasattr(user, "pk") and hasattr(user, "_meta") and user._meta.label == User._meta.label:
            user_obj = user
        else:
            user_obj = None
            user_id = None
    mid = merchant_id
    if mid is not None and hasattr(mid, "pk"):
        mid = mid.pk
    kwargs = {
        "merchant_id": mid,
        "entity": entity,
        "entity_id": entity_id,
        "action": action,
        "old_value": old_value,
        "new_value": new_value,
    }
    if user_obj is not None:
        kwargs["actor_user"] = user_obj
    elif user_id is not None:
        kwargs["actor_user_id"] = user_id
    return AuditEvent.objects.create(**kwargs)
