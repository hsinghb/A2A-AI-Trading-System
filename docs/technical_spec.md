# A2A Technical Specification

## System Architecture

### 1. Agent Identity Management
- **DID Format**: Using `did:ethr` format for agent identities
- **Registry Implementation**: 
  - Local registry with JSON storage
  - Supports both `did:ethr:` and `did:eth:` prefixes
  - Normalizes DIDs for consistent lookup

### 2. Agent Types
- **Orchestrator Agent**
  - Manages communication between expert and risk agents
  - Handles request routing and response aggregation
  - Maintains session state and verification

- **Expert Agent**
  - Analyzes trading requests
  - Provides market analysis and recommendations
  - Verifies orchestrator identity

- **Risk Agent**
  - Evaluates trading risks
  - Provides risk assessment and constraints
  - Verifies orchestrator identity

### 3. Communication Protocol
- **Request Flow**:
  1. Human trader → Orchestrator (with JWT)
  2. Orchestrator → Expert Agent (with orchestrator's JWT)
  3. Orchestrator → Risk Agent (with orchestrator's JWT)
  4. Orchestrator → Human trader (aggregated response)

- **Identity Verification**:
  - JWT-based authentication
  - DID verification through registry
  - Public key validation

### 4. Security Implementation
- **Token Management**:
  - JWT tokens for agent communication
  - Token expiration and rotation
  - Role-based access control

- **Key Management**:
  - Private keys stored securely
  - Public keys in registry
  - Key rotation support

### 5. Current Implementation Status
- **Completed**:
  - Basic agent registry
  - JWT-based authentication
  - Agent communication flow
  - DID normalization

- **In Progress**:
  - Enhanced security measures
  - Improved error handling
  - Session management
  - Performance optimization

### 6. Known Issues and Solutions
1. **DID Prefix Handling**:
   - Issue: Inconsistent DID prefix usage
   - Solution: Normalize all DIDs to `did:eth:` format in registry

2. **Identity Verification**:
   - Issue: Token verification failures
   - Solution: Ensure consistent DID usage in token creation and verification

3. **Agent Communication**:
   - Issue: Incorrect sender identity in requests
   - Solution: Use orchestrator's identity for all agent communications

### 7. Future Enhancements
1. **Smart Contract Integration**:
   - On-chain agent registry
   - Reputation management
   - Service discovery

2. **Networking**:
   - P2P communication layer
   - libp2p integration
   - Distributed agent discovery

3. **Security**:
   - TEE implementation
   - Multi-signature coordination
   - Enhanced key management

## Implementation Guidelines

### 1. Code Organization
- `backend/`: Core server implementation
  - `agent_orchestrator.py`: Orchestrator agent
  - `did_registry.py`: DID management
  - `jwt_utils.py`: Token handling
- `agents/`: Individual agent implementations
  - `expert_trader_agent.py`: Expert agent
  - `risk_agent.py`: Risk agent

### 2. Development Standards
- Use type hints for all Python code
- Implement comprehensive error handling
- Maintain detailed logging
- Follow PEP 8 style guide

### 3. Testing Requirements
- Unit tests for all components
- Integration tests for agent communication
- Security testing for authentication
- Performance testing for scalability

### 4. Deployment Checklist
1. Verify DID registry initialization
2. Check agent identity configuration
3. Test JWT token generation and verification
4. Validate agent communication flow
5. Monitor system logs for errors 