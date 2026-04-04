/**
 * Defly Wallet Integration for CfoE
 * 
 * Supports Defly Wallet (Chrome extension + mobile)
 * Handles browser Tracking Prevention blocking CDN scripts
 */

class AlgorandWalletManager {
    constructor() {
        this.wallet = null;
        this.accountAddress = null;
        this.isConnected = false;
        this.sdkLoaded = false;
        this.sdkLoadFailed = false;

        // Multiple CDN sources for resilience against tracking prevention
        this.cdnSources = [
            'https://cdn.jsdelivr.net/npm/@blockshake/defly-connect@1.1.6/dist/defly-connect.min.js',
            'https://unpkg.com/@blockshake/defly-connect@1.1.6/dist/defly-connect.min.js'
        ];
    }

    async initialize() {
        try {
            const savedAddress = localStorage.getItem('cfoe_wallet_address');
            
            if (savedAddress) {
                this.accountAddress = savedAddress;
                this.isConnected = true;
                await this.notifyBackend(savedAddress);
                return true;
            }
            return false;
        } catch (error) {
            console.error('Wallet initialization failed:', error);
            return false;
        }
    }

    async connect() {
        try {
            // Load Defly Wallet Connect from CDN
            if (!window.DeflyWalletConnect && !this.sdkLoaded) {
                try {
                    await this.loadDeflySDK();
                } catch (sdkError) {
                    console.warn('Defly SDK could not be loaded from any CDN:', sdkError.message);
                    console.warn('Browser Tracking Prevention may be blocking CDN scripts.');
                    console.warn('Falling back to manual wallet address input.');
                    this.sdkLoadFailed = true;
                    return await this.connectManual();
                }
            }

            // If SDK previously failed, use manual
            if (this.sdkLoadFailed && !window.DeflyWalletConnect) {
                return await this.connectManual();
            }

            this.wallet = new window.DeflyWalletConnect({
                chainId: 416002,
                shouldShowSignTxnToast: true
            });

            // Try to reconnect existing session
            try {
                const accounts = await this.wallet.reconnectSession();
                if (accounts && accounts.length > 0) {
                    this.accountAddress = accounts[0];
                    this.isConnected = true;
                    await this.saveSession();
                    await this.notifyBackend(this.accountAddress);
                    return { success: true, address: this.accountAddress };
                }
            } catch (e) {
                console.log('No existing session');
            }

            // Create new connection
            const newAccounts = await this.wallet.connect();
            if (newAccounts && newAccounts.length > 0) {
                this.accountAddress = newAccounts[0];
                this.isConnected = true;
                await this.saveSession();
                await this.notifyBackend(this.accountAddress);
                return { success: true, address: this.accountAddress };
            }
            return { success: false, error: 'No accounts returned' };
        } catch (error) {
            console.error('Defly Wallet connection failed:', error);

            // If SDK-based connection fails, offer manual fallback
            if (!this.sdkLoadFailed) {
                console.log('Attempting manual wallet connection as fallback...');
                return await this.connectManual();
            }

            return { success: false, error: error.message };
        }
    }

    /**
     * Manual wallet address input fallback.
     * Used when the Defly SDK cannot be loaded due to browser Tracking Prevention
     * or other CDN blocking issues.
     */
    async connectManual() {
        return new Promise((resolve) => {
            // Create modal dialog for manual address input
            const overlay = document.createElement('div');
            overlay.id = 'wallet-manual-overlay';
            overlay.style.cssText = `
                position: fixed; inset: 0; z-index: 10000;
                background: rgba(0,0,0,0.7); backdrop-filter: blur(6px);
                display: flex; align-items: center; justify-content: center;
            `;

            const dialog = document.createElement('div');
            dialog.style.cssText = `
                background: var(--surface, #1a1a2e); color: var(--text, #e0e0e0);
                border-radius: 16px; padding: 2rem; max-width: 480px; width: 90%;
                box-shadow: 0 20px 60px rgba(0,0,0,0.5);
                border: 1px solid rgba(255,255,255,0.1);
                font-family: 'Space Grotesk', sans-serif;
            `;

            dialog.innerHTML = `
                <h3 style="margin:0 0 0.5rem; font-size:1.25rem;">🔗 Connect Wallet Manually</h3>
                <p style="margin:0 0 1rem; font-size:0.85rem; opacity:0.7; line-height:1.5;">
                    Your browser's Tracking Prevention blocked the Defly SDK.<br>
                    Paste your Algorand wallet address below to connect directly.
                </p>
                <input id="manual-wallet-input" type="text" placeholder="Algorand address (58 characters)"
                    style="width:100%; padding:0.75rem 1rem; border-radius:8px; border:1px solid rgba(255,255,255,0.2);
                    background:rgba(255,255,255,0.05); color:inherit; font-family:'IBM Plex Mono',monospace;
                    font-size:0.8rem; outline:none; box-sizing:border-box;" />
                <p id="manual-wallet-error" style="color:#ff6b6b; font-size:0.8rem; margin:0.5rem 0; min-height:1.2em;"></p>
                <div style="display:flex; gap:0.75rem; margin-top:1rem;">
                    <button id="manual-wallet-submit" style="flex:1; padding:0.75rem; border:none; border-radius:8px;
                        background:linear-gradient(135deg,#6c5ce7,#a855f7); color:#fff; font-weight:600;
                        cursor:pointer; font-size:0.9rem;">Connect</button>
                    <button id="manual-wallet-cancel" style="flex:1; padding:0.75rem; border:1px solid rgba(255,255,255,0.2);
                        border-radius:8px; background:transparent; color:inherit; cursor:pointer;
                        font-size:0.9rem;">Cancel</button>
                </div>
                <p style="margin:1rem 0 0; font-size:0.75rem; opacity:0.5; text-align:center;">
                    💡 Tip: Disable Tracking Prevention for this site, or use Chrome instead of Edge/Brave.
                </p>
            `;

            overlay.appendChild(dialog);
            document.body.appendChild(overlay);

            const input = document.getElementById('manual-wallet-input');
            const errorEl = document.getElementById('manual-wallet-error');
            const submitBtn = document.getElementById('manual-wallet-submit');
            const cancelBtn = document.getElementById('manual-wallet-cancel');

            input.focus();

            const cleanup = () => {
                overlay.remove();
            };

            const validateAlgorandAddress = (addr) => {
                // Algorand addresses are 58 characters, uppercase A-Z and 2-7
                return /^[A-Z2-7]{58}$/.test(addr);
            };

            submitBtn.addEventListener('click', async () => {
                const address = input.value.trim().toUpperCase();
                errorEl.textContent = '';

                if (!address) {
                    errorEl.textContent = 'Please enter a wallet address.';
                    return;
                }

                if (!validateAlgorandAddress(address)) {
                    errorEl.textContent = 'Invalid Algorand address. Must be 58 characters (A-Z, 2-7).';
                    return;
                }

                this.accountAddress = address;
                this.isConnected = true;
                await this.saveSession();
                await this.notifyBackend(this.accountAddress);
                cleanup();
                resolve({ success: true, address: this.accountAddress, manual: true });
            });

            cancelBtn.addEventListener('click', () => {
                cleanup();
                resolve({ success: false, error: 'User cancelled manual connection' });
            });

            // Allow Enter key to submit
            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') submitBtn.click();
                if (e.key === 'Escape') cancelBtn.click();
            });

            // Close on overlay click
            overlay.addEventListener('click', (e) => {
                if (e.target === overlay) cancelBtn.click();
            });
        });
    }

    /**
     * Load the Defly SDK with multiple CDN fallbacks and retry logic.
     * Uses crossorigin="anonymous" to avoid storage-access issues from Tracking Prevention.
     */
    async loadDeflySDK() {
        for (let attempt = 0; attempt < 2; attempt++) {
            for (const src of this.cdnSources) {
                try {
                    await this._loadScript(src);
                    if (window.DeflyWalletConnect) {
                        this.sdkLoaded = true;
                        console.log(`Defly SDK loaded from: ${src}`);
                        return;
                    }
                } catch (e) {
                    console.warn(`Failed to load Defly SDK from ${src} (attempt ${attempt + 1}):`, e.message);
                }
            }
        }
        throw new Error('Failed to load Defly SDK from all CDN sources. Browser may be blocking third-party scripts.');
    }

    _loadScript(src) {
        return new Promise((resolve, reject) => {
            // Remove any previously failed script tags for this src
            const existing = document.querySelector(`script[src="${src}"]`);
            if (existing) existing.remove();

            const script = document.createElement('script');
            script.src = src;
            script.crossOrigin = 'anonymous';  // Prevent storage-access issues
            script.referrerPolicy = 'no-referrer';  // Reduce tracking signals
            
            const timeout = setTimeout(() => {
                script.remove();
                reject(new Error(`Timeout loading script: ${src}`));
            }, 10000);

            script.onload = () => {
                clearTimeout(timeout);
                resolve();
            };
            script.onerror = () => {
                clearTimeout(timeout);
                script.remove();
                reject(new Error(`Failed to load script: ${src}`));
            };
            document.head.appendChild(script);
        });
    }

    async disconnect() {
        if (this.wallet) {
            try {
                await this.wallet.disconnect();
            } catch (error) {
                console.error('Wallet disconnect error:', error);
            }
        }
        
        this.accountAddress = null;
        this.isConnected = false;
        this.wallet = null;
        this.clearSession();
        await this.notifyBackendDisconnect();
        return { success: true };
    }

    async saveSession() {
        try {
            localStorage.setItem('cfoe_wallet_address', this.accountAddress);
        } catch (e) {
            // localStorage may also be blocked by tracking prevention
            console.warn('Could not save wallet session to localStorage:', e.message);
        }
    }

    clearSession() {
        try {
            localStorage.removeItem('cfoe_wallet_address');
        } catch (e) {
            console.warn('Could not clear wallet session from localStorage:', e.message);
        }
    }

    async notifyBackend(address) {
        try {
            const response = await fetch('/api/wallet/connect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ address })
            });
            return await response.json();
        } catch (error) {
            console.error('Backend notification failed:', error);
        }
    }

    async notifyBackendDisconnect() {
        try {
            const response = await fetch('/api/wallet/disconnect', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            return await response.json();
        } catch (error) {
            console.error('Backend disconnect notification failed:', error);
        }
    }

    getAddress() {
        return this.accountAddress;
    }

    getShortAddress() {
        if (!this.accountAddress) return null;
        return `${this.accountAddress.slice(0, 6)}...${this.accountAddress.slice(-4)}`;
    }
}

window.walletManager = new AlgorandWalletManager();
console.log('Wallet manager initialized:', window.walletManager);
