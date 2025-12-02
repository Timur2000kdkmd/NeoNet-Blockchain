import React, { useState } from 'react';
import { useWallet } from './WalletProvider';

const styles = {
  overlay: {
    position: 'fixed',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    background: 'rgba(0, 0, 0, 0.8)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000
  },
  modal: {
    background: 'linear-gradient(135deg, #1a1a3a 0%, #0a0a2a 100%)',
    borderRadius: '20px',
    padding: '40px',
    maxWidth: '500px',
    width: '90%',
    border: '1px solid rgba(0, 255, 200, 0.3)',
    boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5)'
  },
  title: {
    fontSize: '24px',
    fontWeight: 'bold',
    marginBottom: '24px',
    background: 'linear-gradient(90deg, #00ffc8, #00a8ff)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    textAlign: 'center'
  },
  tabs: {
    display: 'flex',
    gap: '10px',
    marginBottom: '24px'
  },
  tab: {
    flex: 1,
    padding: '12px',
    borderRadius: '8px',
    border: '1px solid rgba(0, 255, 200, 0.2)',
    background: 'transparent',
    color: '#8892b0',
    cursor: 'pointer',
    transition: 'all 0.3s'
  },
  tabActive: {
    background: 'rgba(0, 255, 200, 0.1)',
    color: '#00ffc8',
    border: '1px solid rgba(0, 255, 200, 0.5)'
  },
  input: {
    width: '100%',
    padding: '14px 18px',
    borderRadius: '8px',
    border: '1px solid rgba(0, 255, 200, 0.2)',
    background: 'rgba(0, 0, 0, 0.3)',
    color: '#fff',
    fontSize: '14px',
    marginBottom: '16px',
    outline: 'none',
    resize: 'vertical',
    minHeight: '100px',
    fontFamily: 'monospace'
  },
  button: {
    width: '100%',
    padding: '14px',
    borderRadius: '8px',
    border: 'none',
    background: 'linear-gradient(90deg, #00ffc8, #00a8ff)',
    color: '#0a0a1a',
    fontSize: '16px',
    fontWeight: 'bold',
    cursor: 'pointer',
    transition: 'transform 0.3s, opacity 0.3s',
    marginBottom: '12px'
  },
  buttonSecondary: {
    background: 'transparent',
    border: '1px solid rgba(0, 255, 200, 0.3)',
    color: '#00ffc8'
  },
  mnemonicBox: {
    background: 'rgba(0, 0, 0, 0.4)',
    borderRadius: '12px',
    padding: '20px',
    marginBottom: '20px',
    border: '1px solid rgba(255, 200, 0, 0.3)'
  },
  mnemonicWords: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
    gap: '8px',
    marginTop: '12px'
  },
  word: {
    background: 'rgba(0, 255, 200, 0.1)',
    padding: '8px 12px',
    borderRadius: '6px',
    fontSize: '12px',
    textAlign: 'center',
    fontFamily: 'monospace'
  },
  warning: {
    color: '#ffc800',
    fontSize: '13px',
    marginBottom: '16px',
    display: 'flex',
    alignItems: 'center',
    gap: '8px'
  },
  addressBox: {
    background: 'rgba(0, 0, 0, 0.3)',
    borderRadius: '8px',
    padding: '12px',
    marginBottom: '12px'
  },
  addressLabel: {
    fontSize: '12px',
    color: '#8892b0',
    marginBottom: '4px'
  },
  addressValue: {
    fontSize: '13px',
    fontFamily: 'monospace',
    wordBreak: 'break-all',
    color: '#00ffc8'
  },
  close: {
    position: 'absolute',
    top: '20px',
    right: '20px',
    background: 'transparent',
    border: 'none',
    color: '#8892b0',
    fontSize: '24px',
    cursor: 'pointer'
  },
  error: {
    color: '#ff4757',
    fontSize: '14px',
    marginBottom: '16px',
    textAlign: 'center'
  }
};

export function WalletModal({ isOpen, onClose }) {
  const [tab, setTab] = useState('create');
  const [importMnemonic, setImportMnemonic] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  
  const {
    createNewWallet,
    importWallet,
    isLoading,
    error,
    mnemonic,
    showMnemonic,
    setShowMnemonic,
    addresses,
    isConnected
  } = useWallet();

  if (!isOpen) return null;

  const handleCreate = async () => {
    try {
      await createNewWallet();
    } catch (e) {
      console.error(e);
    }
  };

  const handleImport = async () => {
    try {
      await importWallet(importMnemonic.trim());
      onClose();
    } catch (e) {
      console.error(e);
    }
  };

  const handleConfirmMnemonic = () => {
    setConfirmed(true);
    setShowMnemonic(false);
    onClose();
  };

  const mnemonicWords = mnemonic ? mnemonic.split(' ') : [];

  return (
    <div style={styles.overlay} onClick={onClose}>
      <div style={{ ...styles.modal, position: 'relative' }} onClick={e => e.stopPropagation()}>
        <button style={styles.close} onClick={onClose}>×</button>
        
        <h2 style={styles.title}>NeoNet Web4 Wallet</h2>
        
        {!showMnemonic && !isConnected && (
          <>
            <div style={styles.tabs}>
              <button
                style={{ ...styles.tab, ...(tab === 'create' ? styles.tabActive : {}) }}
                onClick={() => setTab('create')}
              >
                Create New
              </button>
              <button
                style={{ ...styles.tab, ...(tab === 'import' ? styles.tabActive : {}) }}
                onClick={() => setTab('import')}
              >
                Import Wallet
              </button>
            </div>

            {error && <div style={styles.error}>{error}</div>}

            {tab === 'create' && (
              <>
                <p style={{ color: '#8892b0', marginBottom: '20px', fontSize: '14px' }}>
                  Create a new NeoNet wallet with dual keys: EVM (0x...) for Ethereum compatibility 
                  and Quantum-safe (neo1...) for post-quantum security.
                </p>
                <button
                  style={styles.button}
                  onClick={handleCreate}
                  disabled={isLoading}
                >
                  {isLoading ? 'Creating...' : 'Generate New Wallet'}
                </button>
              </>
            )}

            {tab === 'import' && (
              <>
                <p style={{ color: '#8892b0', marginBottom: '16px', fontSize: '14px' }}>
                  Enter your 24-word recovery phrase to restore your wallet.
                </p>
                <textarea
                  style={styles.input}
                  placeholder="Enter your 24-word mnemonic phrase..."
                  value={importMnemonic}
                  onChange={(e) => setImportMnemonic(e.target.value)}
                />
                <button
                  style={styles.button}
                  onClick={handleImport}
                  disabled={isLoading || !importMnemonic.trim()}
                >
                  {isLoading ? 'Restoring...' : 'Import Wallet'}
                </button>
              </>
            )}
          </>
        )}

        {showMnemonic && mnemonic && (
          <>
            <div style={styles.warning}>
              <span>⚠️</span>
              <span>Write down these words in order and store them securely. Never share them!</span>
            </div>
            
            <div style={styles.mnemonicBox}>
              <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '8px' }}>
                Recovery Phrase (24 words)
              </div>
              <div style={styles.mnemonicWords}>
                {mnemonicWords.map((word, i) => (
                  <div key={i} style={styles.word}>
                    <span style={{ color: '#8892b0', marginRight: '4px' }}>{i + 1}.</span>
                    {word}
                  </div>
                ))}
              </div>
            </div>

            <div style={styles.addressBox}>
              <div style={styles.addressLabel}>EVM Address (Ethereum Compatible)</div>
              <div style={styles.addressValue}>{addresses.evmAddress}</div>
            </div>

            <div style={styles.addressBox}>
              <div style={styles.addressLabel}>Quantum Address (Post-Quantum Safe)</div>
              <div style={styles.addressValue}>{addresses.neoAddress}</div>
            </div>

            <button style={styles.button} onClick={handleConfirmMnemonic}>
              I've Saved My Recovery Phrase
            </button>
          </>
        )}

        {isConnected && !showMnemonic && (
          <>
            <div style={{ textAlign: 'center', marginBottom: '20px' }}>
              <div style={{ fontSize: '48px', marginBottom: '12px' }}>✓</div>
              <div style={{ color: '#00ffc8', fontSize: '18px' }}>Wallet Connected!</div>
            </div>

            <div style={styles.addressBox}>
              <div style={styles.addressLabel}>EVM Address</div>
              <div style={styles.addressValue}>{addresses.evmAddress}</div>
            </div>

            <div style={styles.addressBox}>
              <div style={styles.addressLabel}>Quantum Address</div>
              <div style={styles.addressValue}>{addresses.neoAddress}</div>
            </div>

            <button style={styles.button} onClick={onClose}>
              Continue to Dashboard
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default WalletModal;
