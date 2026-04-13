"""
CfoE Carbon Credit Token System - Algorand ASA Integration

Implements tokenized carbon credits using Algorand Standard Assets (ASA):
1. Fungible Carbon Credits (CCT) - Tradeable emission reduction units
2. Audit Certificate NFTs - Unique proof of compliance for each audit
3. Token Transfer & Trading - P2P carbon credit marketplace
4. Retirement/Burn - Permanent removal of used credits

Usage:
    from carbon_token_manager import get_token_manager
    
    tm = get_token_manager()
    
    # Create carbon credit token pool
    asset_id = tm.create_carbon_credit_token(
        total_credits=10_000_000,
        unit_name="CCT",
        asset_name="CfoE Carbon Credit"
    )
    
    # Issue credits to supplier for emissions reduction
    tm.issue_credits(supplier_address, 5000, "Q1 2024 reduction")
    
    # Create audit certificate NFT
    nft_id = tm.create_audit_certificate_nft(
        supplier_name="GreenCorp",
        audit_id="AUD-12345",
        risk_score=0.25,
        metadata_url="ipfs://..."
    )
"""

import os
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()


class CarbonCreditTokenManager:
    """
    Manages tokenized carbon credits and audit certificates on Algorand.
    
    Token Economics:
    - 1 CCT Token = 10 Carbon Credits (tons CO2eq)
    - Example: 5000 tons CO2eq reduction = 500 CCT tokens
    - Fractional tokens supported (0.1 CCT = 1 ton CO2eq)
    
    Features:
    - Fungible carbon credit tokens (ASA) for trading emission reductions
    - NFT audit certificates for compliance proof
    - Credit issuance, transfer, and retirement
    - Integration with CfoE audit pipeline
    """
    
    # Token conversion rate: 1 token = 10 carbon credits (tons CO2eq)
    CREDITS_PER_TOKEN = 10
    
    def __init__(self, blockchain_client):
        self.bc = blockchain_client
        self.carbon_credit_asset_id = None
        self.issued_credits: List[Dict] = []
        self.retired_credits: List[Dict] = []
        self.audit_nfts: List[Dict] = []
        
    # ================================================================== #
    #  CARBON CREDIT TOKEN CREATION
    # ================================================================== #
    
    def create_carbon_credit_token(
        self,
        total_credits: int = 10_000_000,
        decimals: int = 1,
        unit_name: str = "CCT",
        asset_name: str = "CfoE Carbon Credit",
        url: str = "https://cfoe.carbon/credits",
    ) -> Optional[int]:
        """
        Create a fungible carbon credit token (ASA).
        
        Token Economics:
        - 1 CCT Token = 10 Carbon Credits (tons CO2eq)
        - Total supply in tokens = total_credits / 10
        - Example: 10M credits = 1M tokens
        - 1 decimal place allows 0.1 CCT = 1 ton CO2eq
        
        Args:
            total_credits: Total carbon credits in tons CO2eq (default 10M)
            decimals: Decimal places (default 1 for 0.1 precision)
            unit_name: Short ticker symbol (default "CCT")
            asset_name: Full name of the asset
            url: URL with token information
            
        Returns:
            Asset ID of the created token, or None if failed
        """
        if not self.bc.connected or not self.bc.wallet_connected:
            print("  [Token] ERROR: Wallet not connected")
            return None
            
        try:
            from algosdk.transaction import AssetConfigTxn, wait_for_confirmation
            
            params = self.bc.algod_client.suggested_params()
            
            # Calculate total tokens: 1 token = 10 credits
            total_tokens = total_credits // self.CREDITS_PER_TOKEN
            
            # Create asset configuration transaction
            txn = AssetConfigTxn(
                sender=self.bc.address,
                sp=params,
                total=total_tokens * (10 ** decimals),  # Total with decimals
                default_frozen=False,
                unit_name=unit_name,
                asset_name=asset_name,
                manager=self.bc.address,
                reserve=self.bc.address,
                freeze=self.bc.address,
                clawback=self.bc.address,
                url=url,
                decimals=decimals,
            )
            
            env_key = os.getenv("ALGORAND_PRIVATE_KEY")
            if not env_key:
                print("  [Token] ERROR: ALGORAND_PRIVATE_KEY required for token creation")
                return None
                
            signed_txn = txn.sign(env_key)
            tx_id = self.bc.algod_client.send_transaction(signed_txn)
            
            result = wait_for_confirmation(self.bc.algod_client, tx_id, 4)
            asset_id = result["asset-index"]
            
            self.carbon_credit_asset_id = asset_id
            
            print(f"  [Token] CARBON CREDIT TOKEN CREATED")
            print(f"          Asset ID:       {asset_id}")
            print(f"          Name:           {asset_name}")
            print(f"          Symbol:         {unit_name}")
            print(f"          Total Tokens:   {total_tokens:,} CCT")
            print(f"          Total Credits:  {total_credits:,} tons CO2eq")
            print(f"          Rate:           1 CCT = {self.CREDITS_PER_TOKEN} tons CO2eq")
            print(f"          Decimals:       {decimals}")
            print(f"          TX:             {tx_id[:20]}...")
            
            return asset_id
            
        except Exception as e:
            print(f"  [Token] ERROR creating carbon credit token: {e}")
            return None
    
    # ================================================================== #
    #  CREDIT ISSUANCE
    # ================================================================== #
    
    def issue_credits(
        self,
        recipient_address: str,
        carbon_credits: float,
        reason: str,
        audit_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Issue carbon credits by recording them in the ledger (no token transfer).
        
        Token Economics:
        - Input: carbon_credits in tons CO2eq
        - Credits recorded: carbon_credits / 10 CCT tokens
        - Example: 5000 tons CO2eq = 500 CCT tokens
        
        Args:
            recipient_address: Algorand address receiving credits
            carbon_credits: Carbon credits in tons CO2eq
            reason: Reason for issuance
            audit_id: Associated audit ID for traceability
            
        Returns:
            Transaction ID or None if failed
        """
        if not self.carbon_credit_asset_id:
            print("  [Token] ERROR: Carbon credit token not created yet")
            return None
            
        if not self.bc.connected or not self.bc.wallet_connected:
            print("  [Token] ERROR: Wallet not connected")
            return None
            
        try:
            # Convert carbon credits to tokens: 10 credits = 1 token
            tokens = carbon_credits / self.CREDITS_PER_TOKEN
            
            # Record issuance on-chain via note transaction (no asset transfer)
            note_data = {
                "type": "CfoE_CREDIT_ISSUANCE",
                "recipient": recipient_address,
                "carbon_credits": carbon_credits,
                "tokens_issued": tokens,
                "reason": reason,
                "audit_id": audit_id or "N/A",
                "timestamp": datetime.now().isoformat(),
            }
            
            tx_id = self.bc._send_note_tx(note_data)
            
            record = {
                "recipient": recipient_address,
                "carbon_credits": carbon_credits,
                "tokens_issued": tokens,
                "reason": reason,
                "audit_id": audit_id,
                "tx_id": tx_id,
                "timestamp": datetime.now().isoformat(),
            }
            self.issued_credits.append(record)
            
            print(f"  [Token] CREDITS ISSUED")
            print(f"          Recipient:      {recipient_address[:16]}...")
            print(f"          Carbon Credits: {carbon_credits:,.0f} tons CO2eq")
            print(f"          Tokens Issued:  {tokens:,.1f} CCT")
            print(f"          Rate:           1 CCT = {self.CREDITS_PER_TOKEN} tons")
            print(f"          Reason:         {reason}")
            print(f"          Audit:          {audit_id or 'N/A'}")
            if tx_id:
                print(f"          TX:             {tx_id[:20]}...")
            
            return tx_id or "LOCAL"
            
        except Exception as e:
            print(f"  [Token] ERROR issuing credits: {e}")
            return None
    
    # ================================================================== #
    #  CREDIT TRANSFER
    # ================================================================== #

    def transfer_credits(
        self,
        recipient_address: str,
        carbon_credits: float,
        reason: str,
        audit_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Transfer carbon credit tokens to another address.
        
        Token Economics:
        - Input: carbon_credits in tons CO2eq
        - Tokens transferred: carbon_credits / 10
        - Example: 1000 tons CO2eq = 100 CCT tokens transferred
        
        Args:
            recipient_address: Algorand address to receive tokens
            carbon_credits: Carbon credits in tons CO2eq to transfer
            reason: Reason for transfer
            audit_id: Associated audit ID for traceability
            
        Returns:
            Transaction ID or None if failed
        """
        if not self.carbon_credit_asset_id:
            print("  [Token] ERROR: Carbon credit token not created yet")
            return None
            
        if not self.bc.connected or not self.bc.wallet_connected:
            print("  [Token] ERROR: Wallet not connected")
            return None
            
        try:
            from algosdk.transaction import AssetTransferTxn, wait_for_confirmation
            
            params = self.bc.algod_client.suggested_params()
            
            # Convert carbon credits to tokens: 10 credits = 1 token
            tokens = carbon_credits / self.CREDITS_PER_TOKEN
            # Convert to smallest unit (1 decimal place)
            amount_micro = int(tokens * 10)
            
            # Check if user has enough balance
            balance_info = self.get_credit_balance(self.bc.address)
            if balance_info["tokens"] < tokens:
                print(f"  [Token] ERROR: Insufficient balance. Have {balance_info['tokens']:.1f} CCT, need {tokens:.1f} CCT")
                return None
                
            txn = AssetTransferTxn(
                sender=self.bc.address,
                sp=params,
                receiver=recipient_address,
                amt=amount_micro,
                index=self.carbon_credit_asset_id,
                note=json.dumps({
                    "type": "CfoE_CREDIT_TRANSFER",
                    "carbon_credits": carbon_credits,
                    "tokens_transferred": tokens,
                    "reason": reason,
                    "audit_id": audit_id or "N/A",
                    "timestamp": datetime.now().isoformat(),
                }).encode('utf-8')
            )
            
            env_key = os.getenv("ALGORAND_PRIVATE_KEY")
            if not env_key:
                print("  [Token] ERROR: ALGORAND_PRIVATE_KEY required")
                return None
                
            signed_txn = txn.sign(env_key)
            tx_id = self.bc.algod_client.send_transaction(signed_txn)
            
            wait_for_confirmation(self.bc.algod_client, tx_id, 4)
            
            record = {
                "recipient": recipient_address,
                "sender": self.bc.address,
                "carbon_credits": carbon_credits,
                "tokens_transferred": tokens,
                "reason": reason,
                "audit_id": audit_id,
                "tx_id": tx_id,
                "timestamp": datetime.now().isoformat(),
            }
            
            print(f"  [Token] CREDITS TRANSFERRED")
            print(f"          From:           {self.bc.address[:16]}...")
            print(f"          To:             {recipient_address[:16]}...")
            print(f"          Carbon Credits: {carbon_credits:,.0f} tons CO2eq")
            print(f"          Tokens:         {tokens:,.1f} CCT")
            print(f"          Rate:           1 CCT = {self.CREDITS_PER_TOKEN} tons")
            print(f"          Reason:         {reason}")
            print(f"          Audit:          {audit_id or 'N/A'}")
            print(f"          TX:             {tx_id[:20]}...")
            
            return tx_id
            
        except Exception as e:
            print(f"  [Token] ERROR transferring credits: {e}")
            return None


    # ================================================================== #
    #  CREDIT RETIREMENT (BURN)
    # ================================================================== #
    
    def retire_credits(
        self,
        carbon_credits: float,
        reason: str,
        beneficiary: str,
    ) -> Optional[str]:
        """
        Permanently retire (burn) carbon credits by sending to creator (reserve).
        
        Token Economics:
        - Input: carbon_credits in tons CO2eq
        - Tokens retired: carbon_credits / 10
        - Example: 1000 tons CO2eq = 100 CCT tokens retired
        - Tokens are sent back to reserve and marked as retired
        
        Args:
            carbon_credits: Carbon credits to retire in tons CO2eq
            reason: Reason for retirement
            beneficiary: Company/entity benefiting from the offset
            
        Returns:
            Transaction ID or None if failed
        """
        if not self.carbon_credit_asset_id:
            print("  [Token] ERROR: Carbon credit token not created yet")
            return None
            
        if not self.bc.connected or not self.bc.wallet_connected:
            print("  [Token] ERROR: Wallet not connected")
            return None
            
        try:
            from algosdk.transaction import AssetTransferTxn, wait_for_confirmation
            
            # Send tokens back to reserve (creator address) to retire them
            reserve_address = self.bc.address
            params = self.bc.algod_client.suggested_params()
            
            # Convert carbon credits to tokens
            tokens = carbon_credits / self.CREDITS_PER_TOKEN
            amount_micro = int(tokens * 10)
            
            # Check if user has enough balance
            balance_info = self.get_credit_balance(self.bc.address)
            if balance_info["tokens"] < tokens:
                print(f"  [Token] ERROR: Insufficient balance. Have {balance_info['tokens']:.1f} CCT, need {tokens:.1f} CCT")
                return None
            
            txn = AssetTransferTxn(
                sender=self.bc.address,
                sp=params,
                receiver=reserve_address,  # Send to reserve to retire
                amt=amount_micro,
                index=self.carbon_credit_asset_id,
                note=json.dumps({
                    "type": "CfoE_CREDIT_RETIREMENT",
                    "carbon_credits": carbon_credits,
                    "tokens_retired": tokens,
                    "reason": reason,
                    "beneficiary": beneficiary,
                    "timestamp": datetime.now().isoformat(),
                    "status": "PERMANENTLY_RETIRED",
                }).encode('utf-8')
            )
            
            env_key = os.getenv("ALGORAND_PRIVATE_KEY")
            if not env_key:
                print("  [Token] ERROR: ALGORAND_PRIVATE_KEY required")
                return None
                
            signed_txn = txn.sign(env_key)
            tx_id = self.bc.algod_client.send_transaction(signed_txn)
            
            wait_for_confirmation(self.bc.algod_client, tx_id, 4)
            
            record = {
                "carbon_credits": carbon_credits,
                "tokens_retired": tokens,
                "reason": reason,
                "beneficiary": beneficiary,
                "tx_id": tx_id,
                "timestamp": datetime.now().isoformat(),
                "status": "RETIRED",
            }
            self.retired_credits.append(record)
            
            print(f"  [Token] CREDITS RETIRED")
            print(f"          Carbon Credits: {carbon_credits:,.0f} tons CO2eq")
            print(f"          Tokens Retired: {tokens:,.1f} CCT")
            print(f"          Rate:           1 CCT = {self.CREDITS_PER_TOKEN} tons")
            print(f"          Beneficiary:    {beneficiary}")
            print(f"          Reason:         {reason}")
            print(f"          TX:             {tx_id[:20]}...")
            print(f"          Status:         PERMANENTLY RETIRED")
            
            return tx_id
            
        except Exception as e:
            print(f"  [Token] ERROR retiring credits: {e}")
            return None
    
    # ================================================================== #
    #  AUDIT CERTIFICATE NFT
    # ================================================================== #
    
    def create_audit_certificate_nft(
        self,
        supplier_name: str,
        audit_id: str,
        risk_score: float,
        classification: str,
        emissions: float,
        metadata_url: str = "",
    ) -> Optional[int]:
        """
        Create a unique NFT certificate for a completed audit.
        
        Each audit gets a 1-of-1 NFT that proves compliance and can be
        displayed/verified. The NFT contains audit metadata and links to
        the full on-chain audit trail.
        
        Args:
            supplier_name: Name of audited supplier
            audit_id: Unique audit identifier
            risk_score: ESG risk score
            classification: Risk classification
            emissions: CO2 emissions audited
            metadata_url: IPFS/URL with full audit metadata
            
        Returns:
            Asset ID of the NFT, or None if failed
        """
        if not self.bc.connected or not self.bc.wallet_connected:
            print("  [Token] ERROR: Wallet not connected")
            return None
            
        try:
            from algosdk.transaction import AssetConfigTxn, wait_for_confirmation
            
            params = self.bc.algod_client.suggested_params()
            
            # Create metadata hash
            metadata = {
                "supplier": supplier_name,
                "audit_id": audit_id,
                "risk_score": risk_score,
                "classification": classification,
                "emissions": emissions,
                "timestamp": datetime.now().isoformat(),
            }
            metadata_hash = hashlib.sha256(
                json.dumps(metadata).encode('utf-8')
            ).digest()[:32]  # 32 bytes for Algorand
            
            # NFT configuration (total=1, decimals=0)
            txn = AssetConfigTxn(
                sender=self.bc.address,
                sp=params,
                total=1,  # Only 1 NFT
                decimals=0,  # No fractional NFTs
                default_frozen=False,
                unit_name="CFOE",
                asset_name=f"CfoE Audit: {supplier_name[:20]}",
                manager=self.bc.address,
                reserve=self.bc.address,
                freeze=self.bc.address,
                clawback=self.bc.address,
                url=metadata_url or f"https://cfoe.carbon/audit/{audit_id}",
                metadata_hash=metadata_hash,
            )
            
            env_key = os.getenv("ALGORAND_PRIVATE_KEY")
            if not env_key:
                print("  [Token] ERROR: ALGORAND_PRIVATE_KEY required")
                return None
                
            signed_txn = txn.sign(env_key)
            tx_id = self.bc.algod_client.send_transaction(signed_txn)
            
            result = wait_for_confirmation(self.bc.algod_client, tx_id, 4)
            asset_id = result["asset-index"]
            
            record = {
                "asset_id": asset_id,
                "supplier_name": supplier_name,
                "audit_id": audit_id,
                "risk_score": risk_score,
                "classification": classification,
                "emissions": emissions,
                "metadata_url": metadata_url,
                "tx_id": tx_id,
                "timestamp": datetime.now().isoformat(),
            }
            self.audit_nfts.append(record)
            
            print(f"  [Token] AUDIT CERTIFICATE NFT CREATED")
            print(f"          Asset ID:       {asset_id}")
            print(f"          Supplier:       {supplier_name}")
            print(f"          Audit ID:       {audit_id}")
            print(f"          Risk Score:     {risk_score:.2f} ({classification})")
            print(f"          Emissions:      {emissions:,.0f} tons CO2")
            print(f"          TX:             {tx_id[:20]}...")
            
            return asset_id
            
        except Exception as e:
            print(f"  [Token] ERROR creating audit NFT: {e}")
            return None
    
    # ================================================================== #
    #  QUERY & STATUS
    # ================================================================== #
    
    def get_credit_balance(self, address: str) -> Dict[str, float]:
        """Get carbon credit balance for an address.
        
        Returns:
            Dict with tokens and carbon_credits balance
        """
        if not self.carbon_credit_asset_id or not self.bc.connected:
            return {"tokens": 0.0, "carbon_credits": 0.0}
            
        try:
            account_info = self.bc.algod_client.account_info(address)
            assets = account_info.get("assets", [])
            
            for asset in assets:
                if asset["asset-id"] == self.carbon_credit_asset_id:
                    tokens = asset["amount"] / 10  # Convert from micro (1 decimal)
                    carbon_credits = tokens * self.CREDITS_PER_TOKEN
                    return {
                        "tokens": tokens,
                        "carbon_credits": carbon_credits
                    }
                    
            return {"tokens": 0.0, "carbon_credits": 0.0}
            
        except Exception as e:
            print(f"  [Token] ERROR getting balance: {e}")
            return {"tokens": 0.0, "carbon_credits": 0.0}
    
    def get_token_summary(self) -> str:
        """Get formatted summary of token operations."""
        lines = []
        lines.append("=" * 60)
        lines.append("  CARBON CREDIT TOKEN SUMMARY")
        lines.append("=" * 60)
        
        if self.carbon_credit_asset_id:
            lines.append(f"  Carbon Credit Asset ID: {self.carbon_credit_asset_id}")
            lines.append(f"  Total Issued:           {len(self.issued_credits)} transactions")
            lines.append(f"  Total Retired:          {len(self.retired_credits)} transactions")
            lines.append(f"  Audit NFTs Created:     {len(self.audit_nfts)}")
        else:
            lines.append("  No carbon credit token created yet")
            
        if self.issued_credits:
            total_credits = sum(r["carbon_credits"] for r in self.issued_credits)
            total_tokens = sum(r["tokens_issued"] for r in self.issued_credits)
            lines.append(f"\n  Credits Issued:         {total_credits:,.0f} tons CO2eq")
            lines.append(f"  Tokens Issued:          {total_tokens:,.1f} CCT")
            
        if self.retired_credits:
            total_credits = sum(r["carbon_credits"] for r in self.retired_credits)
            total_tokens = sum(r["tokens_retired"] for r in self.retired_credits)
            lines.append(f"  Credits Retired:        {total_credits:,.0f} tons CO2eq")
            lines.append(f"  Tokens Retired:         {total_tokens:,.1f} CCT")
            
        lines.append("=" * 60)
        return "\n".join(lines)


# ================================================================== #
#  SINGLETON
# ================================================================== #

_token_manager_instance = None


def get_token_manager():
    """Get or create the singleton token manager."""
    global _token_manager_instance
    if _token_manager_instance is None:
        from blockchain_client import get_blockchain_client
        bc = get_blockchain_client()
        _token_manager_instance = CarbonCreditTokenManager(bc)
    return _token_manager_instance
