from typing import Dict, Any, List, Optional
from datetime import datetime
import os
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain_core.memory import BaseMemory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.tools import BaseTool

load_dotenv()

class AIBaseAgent:
    def __init__(
        self,
        agent_name: str,
        agent_role: str,
        tools: List[BaseTool],
        memory_key: str = "chat_history",
        temperature: float = 0.7,
        model_name: str = "gpt-4-turbo-preview"
    ):
        self.agent_name = agent_name
        self.agent_role = agent_role
        self.tools = tools
        self.memory_key = memory_key
        self.temperature = temperature
        self.model_name = model_name
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=temperature,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize chat history
        self.chat_history: List[BaseChatMessageHistory] = []
        
        # Initialize vector store for long-term memory
        self.vectorstore = Chroma(
            collection_name=f"{agent_name}_memory",
            embedding_function=OpenAIEmbeddings()
        )
        
        # Create agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are {agent_name}, an AI agent with the following role: {agent_role}
            You have access to the following tools: {[tool.name for tool in tools]}
            Use these tools to accomplish your tasks. Always explain your reasoning before taking actions.
            Maintain a professional and helpful demeanor."""),
            MessagesPlaceholder(variable_name=memory_key),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # Create agent
        self.agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # Create agent executor with memory
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self._get_memory(),
            verbose=True,
            handle_parsing_errors=True
        )
    
    def _get_memory(self) -> BaseMemory:
        """Get memory implementation for the agent."""
        from langchain.memory import ConversationBufferMemory
        
        return ConversationBufferMemory(
            memory_key=self.memory_key,
            return_messages=True,
            output_key="output"
        )
    
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming messages using the AI agent."""
        try:
            # Add message to chat history
            self.chat_history.append(HumanMessage(content=str(message)))
            
            # Process with agent
            response = await self.agent_executor.ainvoke({
                "input": str(message),
                self.memory_key: self.chat_history
            })
            
            # Add response to chat history
            self.chat_history.append(AIMessage(content=str(response)))
            
            # Store in vector memory
            self._store_in_memory(message, response)
            
            return {
                "status": "success",
                "message": "Message processed by AI agent",
                "response": response,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error processing message: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _store_in_memory(self, input_message: Dict[str, Any], response: Dict[str, Any]) -> None:
        """Store interaction in vector memory for long-term retention."""
        metadata = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.agent_name,
            "type": "interaction"
        }
        
        # Store both input and response
        self.vectorstore.add_texts(
            texts=[str(input_message), str(response)],
            metadatas=[metadata, metadata]
        )
    
    def get_memory_context(self, query: str, k: int = 5) -> List[str]:
        """Retrieve relevant memory context for a query."""
        docs = self.vectorstore.similarity_search(query, k=k)
        return [doc.page_content for doc in docs]
    
    def clear_memory(self) -> None:
        """Clear both conversation and vector memory."""
        self.chat_history.clear()
        self.vectorstore.delete_collection()
        self.vectorstore = Chroma(
            collection_name=f"{self.agent_name}_memory",
            embedding_function=OpenAIEmbeddings()
        ) 