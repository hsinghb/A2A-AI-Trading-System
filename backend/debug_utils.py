import json
import logging
import datetime
from typing import Any, Dict, Optional
import streamlit as st
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('trading_system.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('trading_system')

class DebugManager:
    """Manages debugging and logging for the trading system."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.start_time = datetime.datetime.now()
        self.log_entries = []
        self.debug_mode = st.session_state.get('debug_mode', False)
        
        # Create debug directory if it doesn't exist
        self.debug_dir = Path('debug_logs')
        self.debug_dir.mkdir(exist_ok=True)
        
        # Initialize session log file
        self.session_log_file = self.debug_dir / f'session_{session_id}.log'
        
        logger.info(f"Debug session started: {session_id}")
    
    def log_request(self, 
                   endpoint: str, 
                   payload: Dict[str, Any], 
                   headers: Optional[Dict[str, str]] = None) -> None:
        """Log an outgoing request."""
        log_entry = {
            'timestamp': str(datetime.datetime.now()),
            'type': 'request',
            'endpoint': endpoint,
            'payload': payload,
            'headers': headers or {}
        }
        self._log_entry(log_entry)
        
        if self.debug_mode:
            with st.expander(f"🔍 Request to {endpoint}", expanded=False):
                st.json(log_entry)
    
    def log_response(self, 
                    endpoint: str, 
                    status_code: int, 
                    response_data: Any, 
                    headers: Optional[Dict[str, str]] = None) -> None:
        """Log an incoming response."""
        log_entry = {
            'timestamp': str(datetime.datetime.now()),
            'type': 'response',
            'endpoint': endpoint,
            'status_code': status_code,
            'data': response_data,
            'headers': headers or {}
        }
        self._log_entry(log_entry)
        
        if self.debug_mode:
            with st.expander(f"📥 Response from {endpoint} ({status_code})", expanded=False):
                st.json(log_entry)
    
    def log_error(self, 
                  context: str, 
                  error: Exception, 
                  additional_info: Optional[Dict[str, Any]] = None) -> None:
        """Log an error with context."""
        log_entry = {
            'timestamp': str(datetime.datetime.now()),
            'type': 'error',
            'context': context,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'additional_info': additional_info or {}
        }
        self._log_entry(log_entry)
        
        if self.debug_mode:
            with st.expander(f"❌ Error in {context}", expanded=True):
                st.error(f"Error Type: {type(error).__name__}")
                st.error(f"Error Message: {str(error)}")
                if additional_info:
                    st.json(additional_info)
    
    def log_agent_action(self, 
                        agent_type: str, 
                        action: str, 
                        data: Optional[Dict[str, Any]] = None) -> None:
        """Log an agent's action."""
        log_entry = {
            'timestamp': str(datetime.datetime.now()),
            'type': 'agent_action',
            'agent': agent_type,
            'action': action,
            'data': data or {}
        }
        self._log_entry(log_entry)
        
        if self.debug_mode:
            with st.expander(f"🤖 {agent_type} - {action}", expanded=False):
                st.json(log_entry)
    
    def log_state_change(self, 
                        component: str, 
                        old_state: Any, 
                        new_state: Any) -> None:
        """Log a state change."""
        log_entry = {
            'timestamp': str(datetime.datetime.now()),
            'type': 'state_change',
            'component': component,
            'old_state': old_state,
            'new_state': new_state
        }
        self._log_entry(log_entry)
        
        if self.debug_mode:
            with st.expander(f"🔄 State Change in {component}", expanded=False):
                st.json(log_entry)
    
    def _log_entry(self, entry: Dict[str, Any]) -> None:
        """Internal method to log an entry."""
        self.log_entries.append(entry)
        
        # Write to session log file
        with open(self.session_log_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')
        
        # Log to system logger
        logger.debug(f"Session {self.session_id}: {json.dumps(entry)}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the session."""
        return {
            'session_id': self.session_id,
            'start_time': str(self.start_time),
            'end_time': str(datetime.datetime.now()),
            'duration': str(datetime.datetime.now() - self.start_time),
            'total_entries': len(self.log_entries),
            'error_count': sum(1 for entry in self.log_entries if entry['type'] == 'error'),
            'request_count': sum(1 for entry in self.log_entries if entry['type'] == 'request'),
            'response_count': sum(1 for entry in self.log_entries if entry['type'] == 'response')
        }
    
    def display_session_summary(self) -> None:
        """Display a summary of the session in the UI."""
        if self.debug_mode:
            summary = self.get_session_summary()
            with st.expander("📊 Session Summary", expanded=True):
                st.json(summary)
                
                # Display error timeline if there were errors
                if summary['error_count'] > 0:
                    st.subheader("Error Timeline")
                    for entry in self.log_entries:
                        if entry['type'] == 'error':
                            st.error(f"{entry['timestamp']} - {entry['context']}: {entry['error_message']}")
                
                # Display request/response timeline
                st.subheader("Request/Response Timeline")
                for entry in self.log_entries:
                    if entry['type'] in ['request', 'response']:
                        icon = "🔍" if entry['type'] == 'request' else "📥"
                        st.write(f"{icon} {entry['timestamp']} - {entry['endpoint']}")

def setup_debug_mode() -> None:
    """Setup debug mode in the session state."""
    if 'debug_mode' not in st.session_state:
        st.session_state.debug_mode = False

def toggle_debug_mode() -> None:
    """Toggle debug mode."""
    st.session_state.debug_mode = not st.session_state.debug_mode

def get_debug_manager(session_id: str) -> DebugManager:
    """Get or create a debug manager for the session."""
    if 'debug_managers' not in st.session_state:
        st.session_state.debug_managers = {}
    
    if session_id not in st.session_state.debug_managers:
        st.session_state.debug_managers[session_id] = DebugManager(session_id)
    
    return st.session_state.debug_managers[session_id] 