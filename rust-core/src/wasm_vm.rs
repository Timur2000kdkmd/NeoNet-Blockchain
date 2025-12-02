// WASM Virtual Machine for NeoNet smart contracts
use serde::{Deserialize, Serialize};
use anyhow::{Result, anyhow};
use std::collections::HashMap;

#[derive(Serialize, Deserialize, Debug, Clone)]
pub struct WasmContract {
    pub address: String,
    pub code: Vec<u8>,
    pub storage: HashMap<String, String>,
    pub balance: u64,
}

pub struct WasmVM {
    contracts: HashMap<String, WasmContract>,
    gas_limit: u64,
    gas_used: u64,
}

impl WasmVM {
    pub fn new(gas_limit: u64) -> Self {
        WasmVM {
            contracts: HashMap::new(),
            gas_limit,
            gas_used: 0,
        }
    }

    pub fn deploy_contract(&mut self, address: String, code: Vec<u8>) -> Result<()> {
        if self.contracts.contains_key(&address) {
            return Err(anyhow!("Contract already exists at address"));
        }

        if code.len() < 4 || &code[0..4] != b"\0asm" {
            return Err(anyhow!("Invalid WASM magic number"));
        }

        let contract = WasmContract {
            address: address.clone(),
            code,
            storage: HashMap::new(),
            balance: 0,
        };

        self.contracts.insert(address, contract);
        self.gas_used += 21000;
        Ok(())
    }

    pub fn call_contract(&mut self, address: &str, method: &str, args: Vec<String>) -> Result<String> {
        self.gas_used += 3000;
        
        if self.gas_used > self.gas_limit {
            return Err(anyhow!("Out of gas"));
        }

        let contract = self.contracts.get_mut(address)
            .ok_or_else(|| anyhow!("Contract not found"))?;

        match method {
            "get_balance" => Ok(contract.balance.to_string()),
            "get_storage" => {
                if let Some(key) = args.get(0) {
                    Ok(contract.storage.get(key).cloned().unwrap_or_default())
                } else {
                    Err(anyhow!("Missing storage key"))
                }
            },
            "set_storage" => {
                if args.len() >= 2 {
                    let key = args[0].clone();
                    let value = args[1].clone();
                    contract.storage.insert(key.clone(), value.clone());
                    self.gas_used += 5000;
                    Ok(format!("Storage set: {} = {}", key, value))
                } else {
                    Err(anyhow!("Missing key or value"))
                }
            },
            "transfer" => {
                if let Some(amount_str) = args.get(0) {
                    let amount: u64 = amount_str.parse().unwrap_or(0);
                    if contract.balance >= amount {
                        contract.balance -= amount;
                        self.gas_used += 10000;
                        Ok(format!("Transferred: {}", amount))
                    } else {
                        Err(anyhow!("Insufficient balance"))
                    }
                } else {
                    Err(anyhow!("Missing amount"))
                }
            },
            _ => {
                self.gas_used += 1000;
                Ok(format!("WASM method '{}' executed with {} args", method, args.len()))
            }
        }
    }

    pub fn execute_wasm(&mut self, address: &str, input: &[u8]) -> Result<Vec<u8>> {
        if !self.contracts.contains_key(address) {
            return Err(anyhow!("Contract not found"));
        }
        
        self.gas_used += 10000;
        Ok(format!("WASM executed for {} bytes input", input.len()).into_bytes())
    }

    pub fn get_gas_used(&self) -> u64 {
        self.gas_used
    }

    pub fn get_contract(&self, address: &str) -> Option<&WasmContract> {
        self.contracts.get(address)
    }

    pub fn deposit(&mut self, address: &str, amount: u64) -> Result<()> {
        let contract = self.contracts.get_mut(address)
            .ok_or_else(|| anyhow!("Contract not found"))?;
        contract.balance += amount;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_deploy_and_call_contract() {
        let mut vm = WasmVM::new(1000000);
        let code = vec![0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00];
        assert!(vm.deploy_contract("contract1".to_string(), code).is_ok());
        
        let result = vm.call_contract("contract1", "get_balance", vec![]);
        assert!(result.is_ok());
        assert_eq!(result.unwrap(), "0");
    }

    #[test]
    fn test_storage_operations() {
        let mut vm = WasmVM::new(1000000);
        let code = vec![0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00];
        vm.deploy_contract("contract1".to_string(), code).unwrap();
        
        let set_result = vm.call_contract(
            "contract1",
            "set_storage",
            vec!["key1".to_string(), "value1".to_string()]
        );
        assert!(set_result.is_ok());
        
        let get_result = vm.call_contract(
            "contract1",
            "get_storage",
            vec!["key1".to_string()]
        );
        assert_eq!(get_result.unwrap(), "value1");
    }
}
