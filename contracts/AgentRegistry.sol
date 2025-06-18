// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title AgentRegistry

 * @dev Smart contract for managing agent DIDs, public keys, and reputation (single admin version)
 */
contract AgentRegistry {
    // Struct to store agent information
    struct Agent {
        string publicKey;
        uint256 reputation;
        uint256 totalInteractions;
        uint256 successfulInteractions;
        uint256 lastUpdated;
        bool isActive;
        string metadata;  // JSON string for additional metadata
    }
    
    // Mapping from DID to agent address
    mapping(string => address) public didToAddress;
    
    // Mapping from address to agent info
    mapping(address => Agent) public agents;

    // Single admin address
    address public admin;

    // Events
    event AgentRegistered(address indexed agent, string did, string publicKey);
    event AgentUpdated(address indexed agent, string did, string publicKey);
    event ReputationUpdated(address indexed agent, uint256 newScore, bool success);
    event AgentDeactivated(address indexed agent, string did);
    event AdminChanged(address indexed previousAdmin, address indexed newAdmin);

    // Modifiers
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can call this function");
        _;
    }
    
    modifier onlyRegisteredAgent() {
        require(agents[msg.sender].isActive, "Agent not registered or inactive");
        _;
    }
    
    // Constructor
    constructor() {
        admin = msg.sender;
        emit AdminChanged(address(0), msg.sender);
    }

    /**
     * @dev Change the admin address
     * @param newAdmin The new admin address
     */
    function registerAdmin(address newAdmin) external onlyAdmin {
        require(newAdmin != address(0), "New admin cannot be zero address");
        emit AdminChanged(admin, newAdmin);
        admin = newAdmin;
    }
    
    /**
     * @dev Register a new agent
     * @param did The agent's DID
     * @param publicKey The agent's public key
     * @param metadata Additional metadata as JSON string
     */
    function registerAgent(
        string memory did,
        string memory publicKey,
        string memory metadata
    ) external onlyAdmin {
        require(bytes(did).length > 0, "DID cannot be empty");
        require(bytes(publicKey).length > 0, "Public key cannot be empty");
        require(didToAddress[did] == address(0), "DID already registered");
        
        address agentAddress = msg.sender;
        
        // Store agent info
        agents[agentAddress] = Agent({
            publicKey: publicKey,
            reputation: 50,  // Initial reputation score
            totalInteractions: 0,
            successfulInteractions: 0,
            lastUpdated: block.timestamp,
            isActive: true,
            metadata: metadata
        });
        
        // Map DID to address
        didToAddress[did] = agentAddress;
        
        emit AgentRegistered(agentAddress, did, publicKey);
    }
    
    /**
     * @dev Update agent information
     * @param did The agent's DID
     * @param publicKey New public key
     * @param metadata New metadata
     */
    function updateAgent(
        string memory did,
        string memory publicKey,
        string memory metadata
    ) external onlyAdmin {
        address agentAddress = didToAddress[did];
        require(agentAddress != address(0), "DID not registered");
        require(agents[agentAddress].isActive, "Agent is inactive");
        
        Agent storage agent = agents[agentAddress];
        agent.publicKey = publicKey;
        agent.metadata = metadata;
        agent.lastUpdated = block.timestamp;
        
        emit AgentUpdated(agentAddress, did, publicKey);
    }
    
    /**
     * @dev Update agent reputation
     * @param agentAddress The agent's address
     * @param success Whether the interaction was successful
     * @param metadata Additional metadata about the interaction
     */
    function updateReputation(
        address agentAddress,
        bool success,
        string memory metadata
    ) external onlyAdmin {
        require(agents[agentAddress].isActive, "Agent is inactive");
        
        Agent storage agent = agents[agentAddress];
        agent.totalInteractions++;
        
        if (success) {
            agent.successfulInteractions++;
        }
        
        // Calculate new reputation score (0-100)
        agent.reputation = (agent.successfulInteractions * 100) / agent.totalInteractions;
        agent.lastUpdated = block.timestamp;
        
        // Update metadata
        agent.metadata = metadata;
        
        emit ReputationUpdated(agentAddress, agent.reputation, success);
    }
    
    /**
     * @dev Deactivate an agent
     * @param did The agent's DID
     */
    function deactivateAgent(string memory did) external onlyAdmin {
        address agentAddress = didToAddress[did];
        require(agentAddress != address(0), "DID not registered");
        require(agents[agentAddress].isActive, "Agent already inactive");
        
        agents[agentAddress].isActive = false;
        agents[agentAddress].lastUpdated = block.timestamp;
        
        emit AgentDeactivated(agentAddress, did);
    }
    
    /**
     * @dev Get agent information
     * @param did The agent's DID
     * @return agentAddress The agent's address
     * @return publicKey The agent's public key
     * @return reputation The agent's reputation score
     * @return totalInteractions Total number of interactions
     * @return successfulInteractions Number of successful interactions
     * @return lastUpdated Last update timestamp
     * @return isActive Whether the agent is active
     * @return metadata Additional metadata
     */
    function getAgent(string memory did) external view returns (
        address agentAddress,
        string memory publicKey,
        uint256 reputation,
        uint256 totalInteractions,
        uint256 successfulInteractions,
        uint256 lastUpdated,
        bool isActive,
        string memory metadata
    ) {
        agentAddress = didToAddress[did];
        require(agentAddress != address(0), "DID not registered");
        
        Agent storage agent = agents[agentAddress];
        return (
            agentAddress,
            agent.publicKey,
            agent.reputation,
            agent.totalInteractions,
            agent.successfulInteractions,
            agent.lastUpdated,
            agent.isActive,
            agent.metadata
        );
    }
} 