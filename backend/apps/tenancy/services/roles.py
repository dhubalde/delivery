from apps.tenancy.models import EmployeeRole

ROLE_PERMISSIONS = {
    EmployeeRole.Role.ADMIN: {
        "manage_merchant",
        "close_cash",
        "view_analytics",
        "manage_employees",
        "confirm_cash",
        "print_closure",
        "invoice",
        "mark_terminado",
        "view_route",
        "mark_entregado",
        "collect_cash",
        "create_order",
        "edit_order",
        "billing",
        "logistics",
        "preparation",
    },
    EmployeeRole.Role.CAJERO: {"confirm_cash", "print_closure", "invoice", "billing"},
    EmployeeRole.Role.PREPARADOR: {"mark_terminado", "preparation"},
    EmployeeRole.Role.REPARTIDOR: {"view_route", "mark_entregado", "collect_cash", "logistics"},
    EmployeeRole.Role.TOMA_PEDIDOS: {"create_order", "edit_order", "take_orders"},
}

TRANSITION_REQUIRED_ROLES = {
    ("RECIBIDO", "PREPARACION"): {EmployeeRole.Role.ADMIN, EmployeeRole.Role.TOMA_PEDIDOS},
    ("PREPARACION", "FACTURACION"): {EmployeeRole.Role.ADMIN, EmployeeRole.Role.PREPARADOR},
    ("FACTURACION", "LOGISTICA"): {EmployeeRole.Role.ADMIN, EmployeeRole.Role.CAJERO},
    ("LOGISTICA", "ENTREGADO"): {EmployeeRole.Role.ADMIN, EmployeeRole.Role.REPARTIDOR},
    ("RECIBIDO", "CANCELADO"): {
        EmployeeRole.Role.ADMIN,
        EmployeeRole.Role.TOMA_PEDIDOS,
        EmployeeRole.Role.CAJERO,
    },
}


def _role_set(employee):
    if employee is None:
        return set()
    if getattr(employee, "deleted_at", None) is not None:
        return set()
    if not getattr(employee, "is_active", True):
        return set()
    return set(employee.employee_roles.values_list("role", flat=True))


def get_roles(employee):
    return _role_set(employee)


def has_role(employee, role):
    return role in _role_set(employee)


def has_any_role(employee, roles):
    current = _role_set(employee)
    return any(r in current for r in roles)


def effective_permissions(employee):
    perms = set()
    for r in _role_set(employee):
        perms.update(ROLE_PERMISSIONS.get(r, set()))
        perms.add(r)
    return perms


def has_permission(employee, permission):
    return permission in effective_permissions(employee)


def can_transition(employee, from_state, to_state):
    required = TRANSITION_REQUIRED_ROLES.get((from_state, to_state))
    if required is None:
        return False
    return has_any_role(employee, required)


def all_roles():
    return [c[0] for c in EmployeeRole.Role.choices]
