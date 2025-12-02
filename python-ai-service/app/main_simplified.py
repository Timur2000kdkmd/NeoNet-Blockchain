"""
NeoNet AI Service - Web4 Blockchain AI Layer
Proof of Intelligence, Contract Factory, DualGov
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import uuid
import time
import os
import numpy as np

try:
    from .poi_consensus import poi_consensus, contract_auditor, gas_optimizer
    from .contract_factory import contract_factory
    POI_ENABLED = True
except ImportError:
    try:
        from poi_consensus import poi_consensus, contract_auditor, gas_optimizer
        from contract_factory import contract_factory
        POI_ENABLED = True
    except ImportError:
        POI_ENABLED = False
        poi_consensus = contract_auditor = gas_optimizer = contract_factory = None

try:
    from ai_engine import ProofOfIntelligenceEngine, DualGovernance
    AI_ENGINE_ENABLED = True
except ImportError:
    AI_ENGINE_ENABLED = False

try:
    from .federated_learning import fl_engine
    FL_ENABLED = True
except ImportError:
    FL_ENABLED = False
    fl_engine = None

try:
    from .security import attestation, rate_limiter, sandbox, security_monitor
    SECURITY_ENABLED = True
except ImportError:
    SECURITY_ENABLED = False
    attestation = rate_limiter = sandbox = security_monitor = None

try:
    from .neonet_blockchain import blockchain
    BLOCKCHAIN_ENABLED = True
except ImportError:
    try:
        from neonet_blockchain import blockchain
        BLOCKCHAIN_ENABLED = True
    except ImportError:
        BLOCKCHAIN_ENABLED = False
        blockchain = None

app = FastAPI(
    title="NeoNet AI Service - Simplified",
    description="AI-Powered Web4 Blockchain Service",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage для тестирования
miners_storage: Dict[str, dict] = {}
tasks_storage: Dict[str, dict] = {}

class MinerRegister(BaseModel):
    miner_id: Optional[str] = None
    cpu_cores: int
    gpu_memory_mb: int
    endpoint: str

class TaskRequest(BaseModel):
    model_id: str
    payload_ref: str
    priority: int = 1

class BlockValidation(BaseModel):
    block_index: int
    transactions: List[dict]
    proposer: str

@app.get("/")
async def root():
    return {
        "service": "NeoNet AI Service",
        "version": "0.1.0",
        "status": "online",
        "ai_engine_enabled": AI_ENGINE_ENABLED,
        "features": [
            "Proof of Intelligence",
            "Fraud Detection",
            "Gas Optimizer",
            "DualGov (AI + DAO)",
            "Post-Quantum Cryptography"
        ]
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "ai_engine": AI_ENGINE_ENABLED,
        "miners_count": len(miners_storage),
        "tasks_count": len(tasks_storage),
        "timestamp": int(time.time())
    }

@app.post("/register_miner")
async def register_miner(m: MinerRegister):
    miner_uid = m.miner_id or str(uuid.uuid4())
    miners_storage[miner_uid] = {
        "id": miner_uid,
        "cpu_cores": m.cpu_cores,
        "gpu_memory_mb": m.gpu_memory_mb,
        "endpoint": m.endpoint,
        "registered_at": int(time.time())
    }
    return {"miner_uid": miner_uid, "status": "registered"}

@app.get("/miners")
async def list_miners():
    return {"miners": list(miners_storage.values()), "count": len(miners_storage)}

@app.post("/submit_task")
async def submit_task(t: TaskRequest):
    task_id = str(uuid.uuid4())
    tasks_storage[task_id] = {
        "id": task_id,
        "model_id": t.model_id,
        "payload_ref": t.payload_ref,
        "priority": t.priority,
        "state": "queued",
        "created_at": int(time.time())
    }
    return {"task_id": task_id, "status": "queued"}

@app.get("/tasks/{task_id}")
async def get_task(task_id: str):
    if task_id not in tasks_storage:
        raise HTTPException(status_code=404, detail="Task not found")
    return tasks_storage[task_id]

@app.get("/tasks")
async def list_tasks():
    return {"tasks": list(tasks_storage.values()), "count": len(tasks_storage)}

@app.post("/ai/validate_block")
async def validate_block(block: BlockValidation):
    """Proof of Intelligence - AI валидация блока"""
    # Упрощенная логика без реального AI (для MVP)
    confidence_score = 0.95  # В production здесь будет real AI model
    
    is_valid = True
    risk_factors = []
    
    # Проверка на аномалии
    if len(block.transactions) > 1000:
        risk_factors.append("Too many transactions")
        confidence_score -= 0.1
    
    if len(block.proposer) < 10:
        risk_factors.append("Invalid proposer address")
        is_valid = False
        confidence_score = 0.0
    
    return {
        "block_index": block.block_index,
        "is_valid": is_valid,
        "confidence_score": max(0.0, confidence_score),
        "risk_factors": risk_factors,
        "ai_engine": "simplified" if not AI_ENGINE_ENABLED else "full",
        "timestamp": int(time.time())
    }

@app.post("/ai/optimize_gas")
async def optimize_gas(transaction: dict):
    """AI Gas Optimizer"""
    # Упрощенная логика
    base_gas = 21000
    data_gas = len(str(transaction).encode()) * 16
    
    suggested_gas = base_gas + data_gas
    confidence = 0.85
    
    return {
        "suggested_gas_limit": suggested_gas,
        "confidence": confidence,
        "estimated_cost": suggested_gas * 20,  # gwei
        "optimization": "applied",
        "timestamp": int(time.time())
    }

@app.get("/pqc/status")
async def pqc_status():
    """Post-Quantum Cryptography Status"""
    return {
        "status": "enabled",
        "algorithms": [
            "Ed25519 (classical)",
            "Dilithium3 (PQC signatures)",
            "Kyber1024 (PQC key exchange)"
        ],
        "hybrid_mode": True,
        "quantum_safe": True
    }

@app.get("/governance/status")
async def governance_status():
    """DualGov Status"""
    return {
        "model": "DualGov",
        "ai_weight": 0.30,
        "dao_weight": 0.70,
        "proposals_active": 0,
        "last_vote": None
    }

# Federated Learning Endpoints
@app.post("/fl/register")
async def fl_register_node(node_id: str):
    """Register node for federated learning"""
    if not FL_ENABLED or not fl_engine:
        raise HTTPException(status_code=503, detail="Federated learning not enabled")
    
    result = fl_engine.register_node(node_id)
    return result

@app.post("/fl/train")
async def fl_train_local(node_id: str, training_data: List[Dict[str, Any]], 
                         epochs: int = 5, learning_rate: float = 0.001):
    """Train local model on node data"""
    if not FL_ENABLED or not fl_engine:
        raise HTTPException(status_code=503, detail="Federated learning not enabled")
    
    result = fl_engine.train_local_model(node_id, training_data, epochs, learning_rate)
    return result

@app.post("/fl/aggregate")
async def fl_aggregate(node_updates: List[Dict[str, Any]]):
    """Aggregate models from multiple nodes (FedAvg)"""
    if not FL_ENABLED or not fl_engine:
        raise HTTPException(status_code=503, detail="Federated learning not enabled")
    
    result = fl_engine.aggregate_models(node_updates)
    return result

@app.post("/fl/predict")
async def fl_predict(features: List[float]):
    """Predict using global federated model"""
    if not FL_ENABLED or not fl_engine:
        raise HTTPException(status_code=503, detail="Federated learning not enabled")
    
    result = fl_engine.predict(features)
    return result

@app.get("/fl/stats")
async def fl_statistics():
    """Get federated learning statistics"""
    if not FL_ENABLED or not fl_engine:
        raise HTTPException(status_code=503, detail="Federated learning not enabled")
    
    return fl_engine.get_statistics()

@app.get("/fl/model/weights")
async def fl_get_weights():
    """Get current global model weights"""
    if not FL_ENABLED or not fl_engine:
        raise HTTPException(status_code=503, detail="Federated learning not enabled")
    
    return {
        "weights": fl_engine.get_global_model_weights(),
        "training_round": fl_engine.training_rounds
    }

# Security Endpoints
@app.post("/security/attestation/challenge")
async def create_attestation_challenge(node_id: str):
    """Create attestation challenge for node"""
    if not SECURITY_ENABLED or not attestation:
        raise HTTPException(status_code=503, detail="Security module not enabled")
    
    return attestation.create_challenge(node_id)

@app.post("/security/attestation/verify")
async def verify_node_attestation(node_id: str, response: str, stake: int):
    """Verify node attestation"""
    if not SECURITY_ENABLED or not attestation:
        raise HTTPException(status_code=503, detail="Security module not enabled")
    
    return attestation.verify_attestation(node_id, response, stake)

@app.get("/security/attestation/status/{node_id}")
async def check_attestation_status(node_id: str):
    """Check if node is attested"""
    if not SECURITY_ENABLED or not attestation:
        raise HTTPException(status_code=503, detail="Security module not enabled")
    
    return {
        "node_id": node_id,
        "attested": attestation.is_attested(node_id),
        "reputation": attestation.get_reputation(node_id)
    }

@app.post("/security/rate_limit/check")
async def check_rate_limit(client_id: str):
    """Check rate limit for client"""
    if not SECURITY_ENABLED or not rate_limiter:
        raise HTTPException(status_code=503, detail="Security module not enabled")
    
    result = rate_limiter.check_rate_limit(client_id)
    
    if not result["allowed"]:
        raise HTTPException(status_code=429, detail=result)
    
    return result

@app.post("/security/contract/validate")
async def validate_contract(code: str):
    """Validate contract code for security"""
    if not SECURITY_ENABLED or not sandbox:
        raise HTTPException(status_code=503, detail="Security module not enabled")
    
    result = sandbox.validate_contract_code(code)
    
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result)
    
    return result

@app.post("/security/transaction/analyze")
async def analyze_transaction(tx_data: Dict[str, Any]):
    """Analyze transaction for anomalies"""
    if not SECURITY_ENABLED or not security_monitor:
        raise HTTPException(status_code=503, detail="Security module not enabled")
    
    return security_monitor.analyze_transaction_pattern(tx_data)

@app.get("/security/report")
async def security_report():
    """Get security monitoring report"""
    if not SECURITY_ENABLED or not security_monitor:
        raise HTTPException(status_code=503, detail="Security module not enabled")
    
    return security_monitor.get_security_report()

# ===== Proof of Intelligence (PoI) Endpoints =====

class ValidatorRegister(BaseModel):
    validator_id: str
    stake: float
    compute_power: float

class AIProofSubmit(BaseModel):
    validator_id: str
    model_weights: List[float]
    gradients: List[float]
    accuracy: float
    loss: float
    training_rounds: int

@app.post("/poi/validator/register")
async def register_validator(v: ValidatorRegister):
    """Register AI validator for PoI consensus"""
    if not POI_ENABLED or not poi_consensus:
        return {
            "success": True,
            "validator_id": v.validator_id,
            "status": "registered_demo"
        }
    
    success = poi_consensus.register_validator(v.validator_id, v.stake, v.compute_power)
    return {
        "success": success,
        "validator_id": v.validator_id,
        "status": "registered" if success else "already_exists"
    }

@app.post("/poi/proof/submit")
async def submit_ai_proof(proof: AIProofSubmit):
    """Submit AI training proof for block validation"""
    if not POI_ENABLED or not poi_consensus:
        return {
            "success": True,
            "proof_hash": f"demo_{int(time.time())}",
            "status": "submitted_demo"
        }
    
    result = poi_consensus.submit_ai_proof(
        proof.validator_id,
        np.array(proof.model_weights),
        np.array(proof.gradients),
        proof.accuracy,
        proof.loss,
        proof.training_rounds
    )
    
    if result:
        return {
            "success": True,
            "proof": {
                "model_hash": result.model_hash,
                "gradient_hash": result.gradient_hash,
                "accuracy": result.accuracy_score,
                "signature": result.signature
            }
        }
    return {"success": False, "error": "Invalid proof or validator"}

@app.get("/poi/validator/{validator_id}")
async def get_validator_stats(validator_id: str):
    """Get validator statistics"""
    if not POI_ENABLED or not poi_consensus:
        return {
            "validator_id": validator_id,
            "stake": 1000,
            "reputation": 1.0,
            "blocks_validated": 0,
            "status": "demo"
        }
    
    stats = poi_consensus.get_validator_stats(validator_id)
    if stats:
        return stats
    raise HTTPException(status_code=404, detail="Validator not found")

@app.get("/poi/network/stats")
async def get_network_stats():
    """Get PoI network statistics from live blockchain"""
    if BLOCKCHAIN_ENABLED and blockchain:
        stats = blockchain.get_network_stats()
        return {
            "total_validators": stats.get("validators", 21),
            "total_stake": stats.get("total_stake", 45000000),
            "total_compute_power": 100000,
            "current_round": stats.get("current_round", 0),
            "pending_proofs": stats.get("pending_transactions", 0),
            "block_height": stats.get("block_height", 0),
            "total_transactions": stats.get("total_transactions", 0),
            "fraud_detected": stats.get("fraud_detected", 0),
            "attacks_prevented": stats.get("attacks_prevented", 0),
            "ai_decisions": stats.get("ai_decisions", 0),
            "dao_proposals": stats.get("dao_proposals", 0),
            "contracts_deployed": stats.get("contracts_deployed", 0),
            "status": stats.get("status", "healthy")
        }
    
    if POI_ENABLED and poi_consensus:
        return poi_consensus.get_network_stats()
    
    return {
        "total_validators": 21,
        "total_stake": 45000000,
        "total_compute_power": 100000,
        "current_round": 1247892,
        "pending_proofs": 0,
        "status": "demo"
    }

@app.get("/poi/proposer/select")
async def select_proposer():
    """Select next block proposer based on PoI"""
    if not POI_ENABLED or not poi_consensus:
        return {"proposer": "validator_demo_001", "status": "demo"}
    
    proposer = poi_consensus.select_block_proposer()
    return {"proposer": proposer, "status": "selected" if proposer else "insufficient_validators"}

# ===== Contract Auditor Endpoints =====

class ContractAuditRequest(BaseModel):
    bytecode: str

@app.post("/ai/audit_contract")
async def audit_contract(req: ContractAuditRequest):
    """AI-powered smart contract security audit"""
    if not POI_ENABLED or not contract_auditor:
        return {
            "security_score": 0.85,
            "risk_level": "LOW",
            "vulnerabilities": [],
            "recommendation": "APPROVE",
            "status": "demo"
        }
    
    bytecode = bytes.fromhex(req.bytecode.replace("0x", ""))
    return contract_auditor.audit_bytecode(bytecode)

# ===== AI Contract Factory Endpoints =====

class ContractGenerateRequest(BaseModel):
    prompt: str
    type: Optional[str] = "auto"

@app.post("/ai/generate_contract")
async def generate_contract(req: ContractGenerateRequest):
    """Generate smart contract from natural language"""
    if not POI_ENABLED or not contract_factory:
        return {
            "name": "DemoToken",
            "symbol": "DEMO",
            "code": "// Demo contract code",
            "type": "token",
            "status": "demo"
        }
    
    contract = contract_factory.generate(req.prompt)
    return {
        "name": contract.name,
        "symbol": contract.symbol,
        "code": contract.code,
        "abi": contract.abi,
        "type": contract.contract_type,
        "parameters": contract.parameters
    }

@app.get("/ai/factory/stats")
async def contract_factory_stats():
    """Get contract factory statistics"""
    if not POI_ENABLED or not contract_factory:
        return {"total_generated": 0, "by_type": {}, "status": "demo"}
    
    return contract_factory.get_stats()

# ===== Gas Optimizer Endpoints =====

class GasOptimizeRequest(BaseModel):
    network_load: float = 0.5
    pending_txs: int = 100

@app.post("/ai/optimize_gas_v2")
async def optimize_gas_v2(req: GasOptimizeRequest):
    """AI-powered gas price optimization"""
    if not POI_ENABLED or not gas_optimizer:
        return {
            "optimal_gas": 20,
            "base_gas": 20,
            "status": "demo"
        }
    
    optimal = gas_optimizer.predict_optimal_gas(req.network_load, req.pending_txs)
    stats = gas_optimizer.get_gas_stats()
    
    return {
        "optimal_gas": optimal,
        "stats": stats
    }

# ===== NeoNet Contract Deployment =====

class ContractDeployRequest(BaseModel):
    code: str
    runtime: str = "hybrid"  # evm, wasm, or hybrid
    deployer: Optional[str] = None

@app.post("/contracts/deploy")
async def deploy_contract(req: ContractDeployRequest):
    """Deploy smart contract to NeoNet (EVM, WASM, or Hybrid)"""
    if not BLOCKCHAIN_ENABLED or not blockchain:
        return {
            "error": "Blockchain not available",
            "status": "error"
        }
    
    deployer = req.deployer or f"neo1deployer{int(time.time())}"
    result = blockchain.deploy_contract(req.code, req.runtime, deployer)
    return result

@app.get("/contracts")
async def list_contracts():
    """List all deployed contracts"""
    if not BLOCKCHAIN_ENABLED or not blockchain:
        return {"contracts": [], "count": 0}
    
    return {
        "contracts": list(blockchain.contracts.values()),
        "count": len(blockchain.contracts)
    }

@app.get("/contracts/{address}")
async def get_contract(address: str):
    """Get contract details"""
    if not BLOCKCHAIN_ENABLED or not blockchain:
        raise HTTPException(status_code=503, detail="Blockchain not available")
    
    if address not in blockchain.contracts:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    return blockchain.contracts[address]

# ===== DualGov Governance with AI =====

class ProposalCreateRequest(BaseModel):
    title: str
    description: str
    proposer: Optional[str] = None

class VoteRequest(BaseModel):
    proposal_id: str
    voter: str
    vote_for: bool
    stake_weight: float = 1.0

@app.post("/governance/proposals")
async def create_proposal(req: ProposalCreateRequest):
    """Create governance proposal with AI analysis"""
    if not BLOCKCHAIN_ENABLED or not blockchain:
        return {
            "error": "Blockchain not available",
            "status": "error"
        }
    
    proposer = req.proposer or f"neo1proposer{int(time.time())}"
    proposal = blockchain.create_proposal(req.title, req.description, proposer)
    
    return {
        "proposal_id": proposal.proposal_id,
        "title": proposal.title,
        "proposer": proposal.proposer,
        "status": proposal.status,
        "ai_recommendation": proposal.ai_recommendation,
        "ai_confidence": proposal.ai_confidence,
        "voting_ends_at": proposal.voting_ends_at
    }

@app.post("/governance/vote")
async def vote_on_proposal(req: VoteRequest):
    """Vote on proposal (human vote, AI has 30% weight)"""
    if not BLOCKCHAIN_ENABLED or not blockchain:
        return {"error": "Blockchain not available"}
    
    result = blockchain.vote_on_proposal(
        req.proposal_id, req.voter, req.vote_for, req.stake_weight
    )
    return result

@app.get("/governance/proposals")
async def list_proposals():
    """List all governance proposals"""
    if not BLOCKCHAIN_ENABLED or not blockchain:
        return {"proposals": [], "count": 0}
    
    proposals = []
    for p in blockchain.proposals.values():
        proposals.append({
            "proposal_id": p.proposal_id,
            "title": p.title,
            "status": p.status,
            "for_votes": p.for_votes,
            "against_votes": p.against_votes,
            "ai_recommendation": p.ai_recommendation,
            "ai_confidence": p.ai_confidence
        })
    
    return {"proposals": proposals, "count": len(proposals)}

@app.get("/governance/proposals/{proposal_id}")
async def get_proposal(proposal_id: str):
    """Get proposal details"""
    if not BLOCKCHAIN_ENABLED or not blockchain:
        raise HTTPException(status_code=503, detail="Blockchain not available")
    
    if proposal_id not in blockchain.proposals:
        raise HTTPException(status_code=404, detail="Proposal not found")
    
    p = blockchain.proposals[proposal_id]
    return {
        "proposal_id": p.proposal_id,
        "title": p.title,
        "description": p.description,
        "proposer": p.proposer,
        "status": p.status,
        "for_votes": p.for_votes,
        "against_votes": p.against_votes,
        "ai_recommendation": p.ai_recommendation,
        "ai_confidence": p.ai_confidence,
        "ai_weight": p.ai_weight,
        "created_at": p.created_at,
        "voting_ends_at": p.voting_ends_at
    }

# ===== Federated Learning with Real Network Data =====

@app.get("/fl/training-data")
async def get_fl_training_data(limit: int = 500):
    """Get real network data for federated learning training"""
    if not BLOCKCHAIN_ENABLED or not blockchain:
        return {"data": [], "count": 0, "source": "unavailable"}
    
    training_data = blockchain.get_training_data(limit)
    return {
        "data": training_data,
        "count": len(training_data),
        "source": "neonet_blockchain",
        "includes_attacks": any(d.get("attack_type") for d in training_data)
    }

@app.post("/fl/train-on-network")
async def fl_train_on_network(node_id: str, epochs: int = 5):
    """Train federated learning model on real network transaction data"""
    if not FL_ENABLED or not fl_engine:
        raise HTTPException(status_code=503, detail="Federated learning not enabled")
    
    if not BLOCKCHAIN_ENABLED or not blockchain:
        raise HTTPException(status_code=503, detail="Blockchain not available")
    
    training_data = blockchain.get_training_data(500)
    
    result = fl_engine.train_local_model(node_id, training_data, epochs)
    
    return {
        **result,
        "data_source": "neonet_blockchain",
        "fraud_samples": sum(1 for d in training_data if d.get("is_fraud")),
        "attack_samples": sum(1 for d in training_data if d.get("attack_type"))
    }

# ===== Blockchain State =====

@app.get("/blockchain/blocks")
async def get_recent_blocks(limit: int = 10):
    """Get recent blocks from blockchain"""
    if not BLOCKCHAIN_ENABLED or not blockchain:
        return {"blocks": [], "count": 0}
    
    blocks = []
    for block in blockchain.blocks[-limit:]:
        blocks.append({
            "index": block.index,
            "timestamp": block.timestamp,
            "validator": block.validator,
            "hash": block.hash[:16] + "...",
            "tx_count": len(block.transactions),
            "ai_score": block.ai_score
        })
    
    return {"blocks": list(reversed(blocks)), "count": len(blocks)}

@app.get("/blockchain/validators")
async def get_validators():
    """Get all validators"""
    if not BLOCKCHAIN_ENABLED or not blockchain:
        return {"validators": [], "count": 0}
    
    validators = []
    for v in blockchain.validators.values():
        validators.append({
            "address": v.address,
            "stake": v.stake,
            "is_active": v.is_active,
            "blocks_validated": v.blocks_validated,
            "intelligence_score": v.intelligence_score,
            "rewards_earned": v.rewards_earned
        })
    
    validators.sort(key=lambda x: x["stake"], reverse=True)
    return {"validators": validators, "count": len(validators)}

@app.get("/blockchain/transactions")
async def get_recent_transactions(limit: int = 20):
    """Get recent transactions - ALL with hybrid quantum signatures"""
    if not BLOCKCHAIN_ENABLED or not blockchain:
        return {"transactions": [], "count": 0}
    
    transactions = []
    for block in blockchain.blocks[-5:]:
        for tx in block.transactions[-limit:]:
            transactions.append({
                "tx_hash": tx.tx_hash[:16] + "...",
                "sender": tx.sender[:20] + "...",
                "recipient": tx.recipient[:20] + "...",
                "amount": round(tx.amount, 4),
                "tx_type": tx.tx_type,
                "is_fraud": tx.is_fraud,
                "fraud_score": round(tx.fraud_score, 3),
                "timestamp": tx.timestamp,
                # Quantum-safe signatures on ALL transactions
                "signature_algorithm": tx.signature_algorithm,
                "is_verified": tx.is_verified,
                "verification_level": tx.verification_level,
                "has_quantum_sig": bool(tx.quantum_signature),
                "has_dilithium_sig": bool(tx.dilithium_signature)
            })
    
    return {
        "transactions": transactions[-limit:],
        "count": len(transactions[-limit:]),
        "signature_algorithm": "Hybrid-Ed25519+Dilithium3"
    }

@app.post("/blockchain/miners/register")
async def register_blockchain_miner(address: str, cpu_cores: int = 4, 
                                     gpu_memory_mb: int = 8192, endpoint: str = ""):
    """Register AI miner to earn NEO through work"""
    if not BLOCKCHAIN_ENABLED or not blockchain:
        raise HTTPException(status_code=503, detail="Blockchain not available")
    
    result = blockchain.register_miner(address, cpu_cores, gpu_memory_mb, endpoint)
    return result

@app.get("/blockchain/miners")
async def get_blockchain_miners():
    """Get all registered miners"""
    if not BLOCKCHAIN_ENABLED or not blockchain:
        return {"miners": [], "count": 0}
    
    miners = []
    for m in blockchain.miners.values():
        miners.append({
            "address": m.address,
            "cpu_cores": m.cpu_cores,
            "gpu_memory_mb": m.gpu_memory_mb,
            "is_active": m.is_active,
            "tasks_completed": m.tasks_completed,
            "rewards_earned": round(m.rewards_earned, 4),
            "intelligence_contribution": round(m.intelligence_contribution, 4),
            "registered_at": m.registered_at
        })
    
    return {"miners": miners, "count": len(miners)}

@app.post("/blockchain/miners/submit_task")
async def submit_miner_task_result(miner_address: str, task_id: str, 
                                    accuracy: float = 0.8, completion: float = 1.0):
    """Submit AI task result to earn NEO rewards"""
    if not BLOCKCHAIN_ENABLED or not blockchain:
        raise HTTPException(status_code=503, detail="Blockchain not available")
    
    result = blockchain.submit_ai_task_result(
        miner_address, task_id, 
        {"accuracy": accuracy, "completion": completion}
    )
    return result

@app.get("/ai/status")
async def get_ai_status():
    """Get AI autonomous training status"""
    if not BLOCKCHAIN_ENABLED or not blockchain:
        return {"status": "offline", "mode": "unavailable"}
    
    return blockchain.get_ai_status()

# Real blockchain integration - receives blocks from Go Consensus
class IngestBlock(BaseModel):
    index: int
    timestamp: str
    data: str
    prev_hash: str = ""
    hash: str
    nonce: int = 0
    pub_key: str = ""
    signature: str = ""

@app.post("/ingest_block")
async def ingest_block(block: IngestBlock):
    """Receive blocks from Go Consensus for AI fraud detection"""
    # Process block with AI fraud detection
    fraud_score = 0.0
    is_fraud = False
    
    # Simple fraud detection logic
    if block.data:
        # Check for suspicious patterns
        if "steal" in block.data.lower() or "hack" in block.data.lower():
            fraud_score = 0.9
            is_fraud = True
        elif len(block.data) > 10000:
            fraud_score = 0.3
        else:
            fraud_score = 0.05
    
    # Log for AI training
    print(f"[AI] Ingested block {block.index}, fraud_score={fraud_score:.2f}")
    
    return {
        "ok": True,
        "block_index": block.index,
        "ai_processed": True,
        "fraud_score": fraud_score,
        "is_fraud": is_fraud,
        "recommendation": "reject" if is_fraud else "accept"
    }

@app.get("/go_consensus/chain")
async def get_go_consensus_chain():
    """Fetch chain from Go Consensus"""
    import httpx
    go_url = os.getenv("GO_CONSENSUS_URL", "http://127.0.0.1:8080")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{go_url}/chain")
            return resp.json()
    except Exception as e:
        return {"error": str(e), "go_url": go_url}

@app.post("/go_consensus/tx")
async def submit_to_go_consensus(data: str):
    """Submit transaction to Go Consensus"""
    import httpx
    go_url = os.getenv("GO_CONSENSUS_URL", "http://127.0.0.1:8080")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(f"{go_url}/tx", json={"data": data})
            return resp.json()
    except Exception as e:
        return {"error": str(e), "go_url": go_url}

@app.get("/wallet/balance/{address}")
async def get_wallet_balance(address: str):
    """Get wallet balance - earned through mining, staking, or AI training"""
    addr = address.lower()
    
    if BLOCKCHAIN_ENABLED and blockchain:
        balance = blockchain.balances.get(addr, 0)
        return {"address": addr, "balance": balance, "token": "NEO"}
    
    return {"address": addr, "balance": 0, "token": "NEO"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
