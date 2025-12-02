// Post-Quantum Cryptography module for NeoNet
// Full implementation with Dilithium3 signatures and Kyber1024 key exchange
use serde::{Deserialize, Serialize};
use ed25519_dalek::{SigningKey, VerifyingKey, Signature as EdSignature, Signer, Verifier};
use rand::rngs::OsRng;
use anyhow::{Result, anyhow};

// PQC imports
use pqcrypto_dilithium::dilithium3;
use pqcrypto_kyber::kyber1024;
use pqcrypto_traits::sign::{PublicKey as PQPublicKey, SecretKey as PQSecretKey, DetachedSignature};
use pqcrypto_traits::kem::{PublicKey as KemPublicKey, SecretKey as KemSecretKey, Ciphertext, SharedSecret};

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct HybridPublicKey {
    pub ed25519_public: Vec<u8>,
    pub dilithium_public: Vec<u8>,
    pub kyber_public: Vec<u8>,
    pub algorithm: String,
}

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct HybridSignature {
    pub ed25519_sig: Vec<u8>,
    pub dilithium_sig: Vec<u8>,
    pub algorithm: String,
    pub timestamp: u64,
}

pub struct HybridKeyPair {
    ed_signing_key: SigningKey,
    dilithium_public: dilithium3::PublicKey,
    dilithium_secret: dilithium3::SecretKey,
    kyber_public: kyber1024::PublicKey,
    kyber_secret: kyber1024::SecretKey,
}

impl HybridKeyPair {
    /// Generate new hybrid keypair with Ed25519 + Dilithium3 + Kyber1024
    pub fn generate() -> Self {
        let mut rng = OsRng;
        let mut secret_bytes = [0u8; 32];
        rand::RngCore::fill_bytes(&mut rng, &mut secret_bytes);
        let ed_signing_key = SigningKey::from_bytes(&secret_bytes);
        
        // Generate Dilithium3 keypair for signatures
        let (dilithium_public, dilithium_secret) = dilithium3::keypair();
        
        // Generate Kyber1024 keypair for key exchange
        let (kyber_public, kyber_secret) = kyber1024::keypair();
        
        HybridKeyPair {
            ed_signing_key,
            dilithium_public,
            dilithium_secret,
            kyber_public,
            kyber_secret,
        }
    }

    pub fn from_bytes(ed_secret: &[u8]) -> Result<Self> {
        if ed_secret.len() != 32 {
            return Err(anyhow!("Invalid Ed25519 secret key length"));
        }
        
        let secret_bytes: [u8; 32] = ed_secret.try_into()
            .map_err(|_| anyhow!("Invalid secret key bytes"))?;
        let ed_signing_key = SigningKey::from_bytes(&secret_bytes);
        
        // Generate new PQC keys (in production, these should also be restored from storage)
        let (dilithium_public, dilithium_secret) = dilithium3::keypair();
        let (kyber_public, kyber_secret) = kyber1024::keypair();
        
        Ok(HybridKeyPair {
            ed_signing_key,
            dilithium_public,
            dilithium_secret,
            kyber_public,
            kyber_secret,
        })
    }

    pub fn public_key(&self) -> HybridPublicKey {
        HybridPublicKey {
            ed25519_public: self.ed_signing_key.verifying_key().to_bytes().to_vec(),
            dilithium_public: self.dilithium_public.as_bytes().to_vec(),
            kyber_public: self.kyber_public.as_bytes().to_vec(),
            algorithm: "Ed25519+Dilithium3+Kyber1024".to_string(),
        }
    }

    /// Sign message with hybrid signature (Ed25519 + Dilithium3)
    pub fn sign(&self, message: &[u8]) -> HybridSignature {
        // Classical signature
        let ed_sig = self.ed_signing_key.sign(message);
        
        // Post-quantum signature
        let dilithium_sig = dilithium3::detached_sign(message, &self.dilithium_secret);
        
        HybridSignature {
            ed25519_sig: ed_sig.to_bytes().to_vec(),
            dilithium_sig: dilithium_sig.as_bytes().to_vec(),
            algorithm: "Ed25519+Dilithium3".to_string(),
            timestamp: std::time::SystemTime::now()
                .duration_since(std::time::UNIX_EPOCH)
                .unwrap()
                .as_secs(),
        }
    }

    pub fn secret_bytes(&self) -> Vec<u8> {
        self.ed_signing_key.to_bytes().to_vec()
    }
    
    /// Kyber1024 key encapsulation
    pub fn kyber_encapsulate(&self) -> (Vec<u8>, Vec<u8>) {
        let (shared_secret, ciphertext) = kyber1024::encapsulate(&self.kyber_public);
        (shared_secret.as_bytes().to_vec(), ciphertext.as_bytes().to_vec())
    }
    
    /// Kyber1024 key decapsulation
    pub fn kyber_decapsulate(&self, ciphertext: &[u8]) -> Result<Vec<u8>> {
        if ciphertext.len() != kyber1024::ciphertext_bytes() {
            return Err(anyhow!("Invalid Kyber ciphertext length"));
        }
        
        let ct = kyber1024::Ciphertext::from_bytes(ciphertext)
            .map_err(|_| anyhow!("Failed to parse Kyber ciphertext"))?;
        
        let shared_secret = kyber1024::decapsulate(&ct, &self.kyber_secret);
        Ok(shared_secret.as_bytes().to_vec())
    }
}

/// Verify hybrid signature (both Ed25519 and Dilithium3 must be valid)
pub fn verify_hybrid_signature(
    public_key: &HybridPublicKey,
    message: &[u8],
    signature: &HybridSignature
) -> Result<bool> {
    // Verify Ed25519 signature
    if public_key.ed25519_public.len() != 32 {
        return Err(anyhow!("Invalid Ed25519 public key length"));
    }

    let ed_public_bytes: [u8; 32] = public_key.ed25519_public.as_slice().try_into()
        .map_err(|_| anyhow!("Invalid public key bytes"))?;
    let ed_public = VerifyingKey::from_bytes(&ed_public_bytes)
        .map_err(|e| anyhow!("Invalid Ed25519 public key: {}", e))?;
    
    if signature.ed25519_sig.len() != 64 {
        return Err(anyhow!("Invalid Ed25519 signature length"));
    }

    let sig_bytes: [u8; 64] = signature.ed25519_sig.as_slice().try_into()
        .map_err(|_| anyhow!("Invalid signature bytes"))?;
    let ed_sig = EdSignature::from_bytes(&sig_bytes);
    
    // Ed25519 verification
    if ed_public.verify(message, &ed_sig).is_err() {
        return Ok(false);
    }
    
    // Verify Dilithium3 signature
    if signature.dilithium_sig.len() != dilithium3::signature_bytes() {
        return Err(anyhow!("Invalid Dilithium signature length"));
    }
    
    let dil_public = dilithium3::PublicKey::from_bytes(&public_key.dilithium_public)
        .map_err(|_| anyhow!("Failed to parse Dilithium public key"))?;
    
    let dil_sig = dilithium3::DetachedSignature::from_bytes(&signature.dilithium_sig)
        .map_err(|_| anyhow!("Failed to parse Dilithium signature"))?;
    
    // Dilithium3 verification - both signatures must be valid
    match dilithium3::verify_detached_signature(&dil_sig, message, &dil_public) {
        Ok(_) => Ok(true),
        Err(_) => Ok(false),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_keygen_and_sign() {
        let keypair = HybridKeyPair::generate();
        let message = b"NeoNet: Web4 Blockchain with PQC";
        
        let signature = keypair.sign(message);
        let public_key = keypair.public_key();
        
        let is_valid = verify_hybrid_signature(&public_key, message, &signature).unwrap();
        assert!(is_valid);
        assert_eq!(public_key.algorithm, "Ed25519+Dilithium3+Kyber1024");
    }

    #[test]
    fn test_invalid_signature() {
        let keypair1 = HybridKeyPair::generate();
        let keypair2 = HybridKeyPair::generate();
        
        let message = b"Test message";
        let signature = keypair1.sign(message);
        let public_key2 = keypair2.public_key();
        
        let is_valid = verify_hybrid_signature(&public_key2, message, &signature).unwrap();
        assert!(!is_valid);
    }

    #[test]
    fn test_from_bytes() {
        let keypair1 = HybridKeyPair::generate();
        let secret_bytes = keypair1.secret_bytes();
        
        let keypair2 = HybridKeyPair::from_bytes(&secret_bytes).unwrap();
        
        let message = b"Restore test";
        let sig1 = keypair1.sign(message);
        let sig2 = keypair2.sign(message);
        
        // Ed25519 signatures should match
        assert_eq!(sig1.ed25519_sig, sig2.ed25519_sig);
    }
    
    #[test]
    fn test_kyber_kem() {
        let keypair = HybridKeyPair::generate();
        
        // Encapsulate
        let (shared_secret1, ciphertext) = keypair.kyber_encapsulate();
        
        // Decapsulate
        let shared_secret2 = keypair.kyber_decapsulate(&ciphertext).unwrap();
        
        // Shared secrets should match
        assert_eq!(shared_secret1, shared_secret2);
        assert_eq!(shared_secret1.len(), kyber1024::shared_secret_bytes());
    }
    
    #[test]
    fn test_signature_components() {
        let keypair = HybridKeyPair::generate();
        let message = b"Component test";
        
        let signature = keypair.sign(message);
        
        // Check signature lengths
        assert_eq!(signature.ed25519_sig.len(), 64);
        assert_eq!(signature.dilithium_sig.len(), dilithium3::signature_bytes());
        assert!(signature.timestamp > 0);
    }
}
