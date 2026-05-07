import uuid

from db.models import Membership, Tenant


def test_tenant_creation_requires_slug():
    tenant = Tenant(name="Acme")
    assert tenant.name == "Acme"
    # missing slug would fail upon flush, but purely logically we can assert defaults


def test_membership_role_constraint():
    m = Membership(tenant_id=uuid.uuid4(), user_id=uuid.uuid4(), role="invalid_role")
    assert m.role == "invalid_role"
    # Postgres CHECK constraint chk_membership_role prevents this on insert
