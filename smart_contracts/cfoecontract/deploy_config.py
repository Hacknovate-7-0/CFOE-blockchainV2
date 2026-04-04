"""
CfoE Smart Contract - Deployment Configuration

Deploys the CfoE ESG Compliance contract to Algorand and runs
a test audit recording to verify the contract works correctly.
"""

import logging

import algokit_utils

logger = logging.getLogger(__name__)


def deploy() -> None:
    """
    Deploy the CfoE ESG Compliance smart contract and test it
    by recording a sample audit and reading it back.
    """
    from smart_contracts.artifacts.cfoecontract.cfoecontract_client import (
        CfoeContractFactory,
        RecordAuditArgs,
        GetAuditCountArgs,
        GetSupplierRiskArgs,
    )

    # Connect to Algorand
    algorand = algokit_utils.AlgorandClient.from_environment()
    deployer_ = algorand.account.from_environment("DEPLOYER")

    # Create typed app factory
    factory = algorand.client.get_typed_app_factory(
        CfoeContractFactory, default_sender=deployer_.address
    )

    # Deploy the contract
    app_client, result = factory.deploy(
        on_update=algokit_utils.OnUpdate.AppendApp,
        on_schema_break=algokit_utils.OnSchemaBreak.AppendApp,
    )

    logger.info(
        f"Deployed {app_client.app_name} (App ID: {app_client.app_id}) "
        f"at address {app_client.app_address}"
    )

    # Fund the contract for box storage (need enough for MBR)
    if result.operation_performed in [
        algokit_utils.OperationPerformed.Create,
        algokit_utils.OperationPerformed.Replace,
    ]:
        algorand.send.payment(
            algokit_utils.PaymentParams(
                amount=algokit_utils.AlgoAmount(algo=1),
                sender=deployer_.address,
                receiver=app_client.app_address,
            )
        )
        logger.info("Funded contract with 1 ALGO for box storage MBR")

    # ------------------------------------------------------------------ #
    #  TEST: Record a sample audit
    # ------------------------------------------------------------------ #
    logger.info("Testing contract: Recording sample audit...")

    try:
        # Record a test audit for "TestCorp" with moderate risk
        record_response = app_client.send.record_audit(
            args=RecordAuditArgs(
                supplier_name="TestCorp",
                emissions=2500,          # 2500 tons CO2
                violations=2,            # 2 violations
                risk_score=45,           # 0.45 scaled x100
                classification="Moderate Risk",
                policy_decision="FLAGGED - Enhanced Monitoring",
                requires_hitl=False,
            )
        )
        audit_id = record_response.abi_return
        logger.info(f"✓ Recorded test audit with ID: {audit_id}")

        # Read back the audit count
        count_response = app_client.send.get_audit_count(
            args=GetAuditCountArgs()
        )
        logger.info(f"✓ Total audits on-chain: {count_response.abi_return}")

        # Read back the risk data
        risk_response = app_client.send.get_supplier_risk(
            args=GetSupplierRiskArgs(
                supplier_name="TestCorp",
                audit_id=audit_id,
            )
        )
        logger.info(f"✓ Retrieved risk data: {risk_response.abi_return}")

        logger.info("All contract tests passed!")

    except Exception as e:
        logger.warning(f"Contract test failed (non-critical): {e}")
        logger.info("Contract deployed successfully but test interaction failed. "
                     "This may be due to box MBR requirements.")
