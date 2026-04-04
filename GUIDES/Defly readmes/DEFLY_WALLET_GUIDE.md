# Defly Wallet Setup Guide for CfoE

## Quick Start (3 Steps)

### 1. Install Defly Wallet Extension

**Install from Chrome Web Store:**
https://chromewebstore.google.com/detail/defly-wallet/

Or search "Defly Wallet" in Chrome Web Store

### 2. Setup Testnet

1. Open Defly Wallet extension
2. Create new wallet or import existing
3. Click Settings (gear icon)
4. Select **TestNet** network
5. Copy your wallet address

### 3. Get Testnet ALGO

1. Visit: https://bank.testnet.algorand.network/
2. Paste your Defly wallet address
3. Click "Dispense"
4. Wait 10-15 seconds
5. Check balance in Defly Wallet (should show ~10 ALGO)

---

## Connect to CfoE

1. Start CfoE:
   ```bash
   uvicorn webapp:app --reload
   ```

2. Open http://127.0.0.1:8000

3. In **Blockchain Status** panel:
   - Click **"Connect Defly Wallet"**
   - Approve in Defly Wallet popup

4. ✅ Connected! Your address shows in the panel

---

## Using Defly Wallet

### Running Audits

1. Fill audit form
2. Click "Run Audit"
3. Defly Wallet popup appears
4. Review transaction details
5. Click "Approve"
6. Transaction submitted to blockchain
7. View TX on AlgoExplorer

### Viewing Transactions

**In Defly Wallet:**
- Click "Activity" tab
- See all your transactions
- Click any TX for details

**On AlgoExplorer:**
- Copy TX ID from CfoE
- Visit: https://testnet.algoexplorer.io/
- Paste TX ID in search
- View full transaction details

---

## Troubleshooting

**Extension not detected?**
- Refresh the page
- Check extension is enabled
- Try restarting browser

**Connection fails?**
- Ensure TestNet selected in Defly
- Check wallet is unlocked
- Try disconnecting and reconnecting

**Transaction fails?**
- Check you have testnet ALGO
- Verify network is TestNet
- Ensure sufficient balance (>0.1 ALGO)

**Balance shows 0?**
- Wait 10-15 seconds after dispenser
- Refresh Defly Wallet
- Check correct network (TestNet)

---

## Why Defly Wallet?

✅ **Chrome Extension** - Desktop browser support  
✅ **Mobile App** - iOS and Android  
✅ **Fast** - Instant popup approval  
✅ **Simple** - Clean, easy interface  
✅ **Testnet Support** - Easy network switching  
✅ **Free** - No cost to use  

---

## Resources

- **Defly Wallet:** https://defly.app/
- **Chrome Store:** Search "Defly Wallet"
- **Testnet Dispenser:** https://bank.testnet.algorand.network/
- **AlgoExplorer:** https://testnet.algoexplorer.io/
- **Algorand Docs:** https://developer.algorand.org/

---

## Next Steps

1. ✅ Install Defly Wallet extension
2. ✅ Switch to TestNet
3. ✅ Get testnet ALGO
4. ✅ Connect to CfoE
5. ✅ Run your first audit!

**Ready to start!** 🚀
