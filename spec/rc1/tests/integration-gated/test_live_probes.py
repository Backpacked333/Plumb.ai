"""Integration-gated probes. Each is a named gate in acceptance/production-catalog.md; none runs locally."""
import pytest

GATES = [
    ("IG-001", "google_workspace:gmail.messages.send on the customer account with template-only scope; verify message id read-back"),
    ("IG-002", "google_drive:changes.watch delivers a change for a file in an authorized client folder within 15 minutes"),
    ("IG-003", "quickbooks_online:cdc returns Purchase changes for a 20-day window on realm 4011 (30-day look-back, 1,000 objects per response)"),
    ("IG-004", "quickbooks_online:webhooks deliver and verify HMAC for the subscribed entities"),
    ("IG-005", "plaid statements/list and statements/download for an institution on Plaid's supported list, with client Link consent"),
    ("IG-006", "pulumi automation preview/apply/refresh with delegated credentials and state lock on the tenant stack"),
    ("IG-007", "provider training adapter: submit, poll, cancel, cleanup with persisted submission identity"),
    ("IG-008", "PostgreSQL migrations apply in order; RLS policies deny cross-tenant SELECT under the runtime role"),
    ("IG-009", "sandbox egress allow-list blocks an unlisted destination from generated code"),
    ("IG-010", "revocation reaches queued dispatch within the SLA on the deployed control service"),
]


@pytest.mark.integration_gated
@pytest.mark.parametrize("gate_id,description", GATES)
def test_integration_gate(gate_id, description):
    pytest.skip(f"{gate_id} requires a live account or deployed environment: {description}")
