"""
CfoE - Carbon Footprint Optimization Engine
Algorand Smart Contract for ESG Compliance Audit Recording

This contract provides on-chain, immutable, auditable records of ESG supplier
audits performed by the CfoE multi-agent system. It stores risk scores,
classifications, policy decisions, and HITL approvals on the Algorand blockchain.

Key Design Decisions:
- UInt64 for numeric values (risk scores scaled x100: 0.85 → 85)
- Global state for counters and admin address
- Local state not used (stateless per-user)
- Box storage for individual audit records
- Admin-gated write operations for security
"""

from algopy import (
    ARC4Contract,
    BoxMap,
    Global,
    GlobalState,
    Txn,
    UInt64,
    arc4,
    gtxn,
    op,
    subroutine,
)
from algopy.arc4 import String, UInt64 as ARC4UInt64, Bool, abimethod


class CfoeContract(ARC4Contract):
    """
    CfoE ESG Compliance Smart Contract

    Records supplier ESG audit results on the Algorand blockchain for
    immutable compliance tracking and regulatory audit trails.
    """

    def __init__(self) -> None:
        # Global state
        self.total_audits = GlobalState(UInt64(0))
        self.admin = GlobalState(Global.creator_address)

        # Box storage for audit records
        # Key format: supplier_name + "_" + audit_id (as string bytes)
        # Value format: packed data as bytes
        self.audit_scores = BoxMap(arc4.String, ARC4UInt64, key_prefix=b"s_")
        self.audit_classifications = BoxMap(arc4.String, arc4.String, key_prefix=b"c_")
        self.audit_decisions = BoxMap(arc4.String, arc4.String, key_prefix=b"d_")
        self.audit_emissions = BoxMap(arc4.String, ARC4UInt64, key_prefix=b"e_")
        self.audit_violations = BoxMap(arc4.String, ARC4UInt64, key_prefix=b"v_")
        self.audit_hitl_required = BoxMap(arc4.String, arc4.Bool, key_prefix=b"h_")
        self.audit_hitl_approved = BoxMap(arc4.String, arc4.Bool, key_prefix=b"a_")
        self.audit_timestamps = BoxMap(arc4.String, ARC4UInt64, key_prefix=b"t_")

    # ------------------------------------------------------------------ #
    #  WRITE METHODS (admin-gated)
    # ------------------------------------------------------------------ #

    @abimethod()
    def record_audit(
        self,
        supplier_name: arc4.String,
        emissions: ARC4UInt64,
        violations: ARC4UInt64,
        risk_score: ARC4UInt64,
        classification: arc4.String,
        policy_decision: arc4.String,
        requires_hitl: arc4.Bool,
    ) -> ARC4UInt64:
        """
        Record a complete ESG audit on-chain.

        Args:
            supplier_name: Name of the audited supplier
            emissions: Annual CO2 emissions in tons
            violations: Number of regulatory violations
            risk_score: ESG risk score scaled x100 (0-100)
            classification: Risk classification (Low/Moderate/Critical)
            policy_decision: Policy enforcement decision string
            requires_hitl: Whether human-in-the-loop approval is needed

        Returns:
            The audit_id (sequential counter) assigned to this record
        """
        # Admin check
        assert Txn.sender == self.admin, "Only admin can record audits"

        # Increment audit counter
        current_id = self.total_audits.value
        new_id = current_id + UInt64(1)
        self.total_audits.value = new_id

        # Build box key: supplier_name + "_" + audit_id
        audit_id_str = arc4.String(_uint64_to_string(new_id))
        box_key = _build_key(supplier_name, audit_id_str)

        # Store audit data in separate boxes
        self.audit_scores[box_key] = risk_score
        self.audit_classifications[box_key] = classification
        self.audit_decisions[box_key] = policy_decision
        self.audit_emissions[box_key] = emissions
        self.audit_violations[box_key] = violations
        self.audit_hitl_required[box_key] = requires_hitl
        self.audit_hitl_approved[box_key] = arc4.Bool(False)  # Not yet approved
        self.audit_timestamps[box_key] = ARC4UInt64(Global.latest_timestamp)

        return ARC4UInt64(new_id)

    @abimethod()
    def approve_hitl(
        self,
        supplier_name: arc4.String,
        audit_id: ARC4UInt64,
        approved: arc4.Bool,
    ) -> arc4.String:
        """
        Record human-in-the-loop approval or rejection for a critical audit.

        Args:
            supplier_name: Name of the supplier
            audit_id: The audit ID to approve/reject
            approved: True = approved, False = rejected

        Returns:
            Confirmation message
        """
        # Admin check
        assert Txn.sender == self.admin, "Only admin can approve HITL"

        # Build box key
        audit_id_str = arc4.String(_uint64_to_string(audit_id.native))
        box_key = _build_key(supplier_name, audit_id_str)

        # Verify audit exists
        assert box_key in self.audit_scores, "Audit record not found"

        # Verify HITL was required
        assert self.audit_hitl_required[box_key] == arc4.Bool(
            True
        ), "HITL not required for this audit"

        # Record approval
        self.audit_hitl_approved[box_key] = approved

        if approved == arc4.Bool(True):
            return arc4.String("HITL_APPROVED")
        else:
            return arc4.String("HITL_REJECTED")

    @abimethod()
    def update_admin(self, new_admin: arc4.Address) -> None:
        """
        Transfer admin rights to a new address.
        Only callable by the current admin.

        Args:
            new_admin: The new admin address
        """
        assert Txn.sender == self.admin, "Only current admin can transfer"
        self.admin.value = new_admin.native

    # ------------------------------------------------------------------ #
    #  READ METHODS
    # ------------------------------------------------------------------ #

    @abimethod(readonly=True)
    def get_audit_count(self) -> ARC4UInt64:
        """Returns total number of audits recorded on-chain."""
        return ARC4UInt64(self.total_audits.value)

    @abimethod(readonly=True)
    def get_supplier_risk(
        self,
        supplier_name: arc4.String,
        audit_id: ARC4UInt64,
    ) -> arc4.Tuple[ARC4UInt64, arc4.String, arc4.String, arc4.Bool]:
        """
        Retrieve risk data for a specific supplier audit.

        Args:
            supplier_name: Supplier name
            audit_id: The audit ID

        Returns:
            Tuple of (risk_score, classification, policy_decision, hitl_approved)
        """
        audit_id_str = arc4.String(_uint64_to_string(audit_id.native))
        box_key = _build_key(supplier_name, audit_id_str)

        assert box_key in self.audit_scores, "Audit record not found"

        return arc4.Tuple(
            (
                self.audit_scores[box_key],
                self.audit_classifications[box_key],
                self.audit_decisions[box_key],
                self.audit_hitl_approved[box_key],
            )
        )

    @abimethod(readonly=True)
    def get_audit_details(
        self,
        supplier_name: arc4.String,
        audit_id: ARC4UInt64,
    ) -> arc4.Tuple[ARC4UInt64, ARC4UInt64, ARC4UInt64, arc4.Bool, ARC4UInt64]:
        """
        Retrieve full audit details for a supplier.

        Args:
            supplier_name: Supplier name
            audit_id: The audit ID

        Returns:
            Tuple of (emissions, violations, risk_score, hitl_required, timestamp)
        """
        audit_id_str = arc4.String(_uint64_to_string(audit_id.native))
        box_key = _build_key(supplier_name, audit_id_str)

        assert box_key in self.audit_scores, "Audit record not found"

        return arc4.Tuple(
            (
                self.audit_emissions[box_key],
                self.audit_violations[box_key],
                self.audit_scores[box_key],
                self.audit_hitl_required[box_key],
                self.audit_timestamps[box_key],
            )
        )


# ------------------------------------------------------------------ #
#  HELPER SUBROUTINES
# ------------------------------------------------------------------ #


@subroutine
def _uint64_to_string(value: UInt64) -> str:
    """Convert a UInt64 to its decimal string representation."""
    if value == UInt64(0):
        return "0"

    digits = b""
    remaining = value
    while remaining > UInt64(0):
        digit = remaining % UInt64(10)
        remaining = remaining // UInt64(10)
        digits = op.itob(digit)[7:8] + digits  # single byte for digit

    # Convert raw bytes to string - strip leading zeros from itob
    return digits.decode()


@subroutine
def _build_key(supplier_name: arc4.String, audit_id_str: arc4.String) -> arc4.String:
    """Build a box key from supplier name and audit ID."""
    # Simple concatenation with separator
    return arc4.String(supplier_name.native + "_" + audit_id_str.native)
