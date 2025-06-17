from typing import Dict, Any
from datetime import datetime
from .base_agent import BaseAgent

class TriggerAgent(BaseAgent):
    def __init__(self, did: str, name: str = "TriggerAgent"):
        super().__init__(did, name)
        
    async def process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming messages and create trading requests. Requires ask_id for session tracking."""
        ask_id = message.get('ask_id')
        sender_did = message.get('sender_did')
        sender_token = message.get('token')
        sender_public_key = message.get('public_key')
        if not ask_id or not sender_did or not sender_token or not sender_public_key:
            return {
                'status': 'error',
                'message': 'Missing ask_id, sender_did, token, or public_key'
            }
        # Verify sender for this ask/session
        if not self.is_verified(ask_id, sender_did):
            if not self.verify_agent(ask_id, sender_did, sender_token, sender_public_key, algorithm='RS256'):
                return {
                    'status': 'error',
                    'message': 'DID/JWT verification failed'
                }
        if message.get('type') == 'trading_request':
            trading_request = {
                'type': 'trading_request',
                'goals': message.get('goals', {}),
                'constraints': message.get('constraints', {}),
                'timestamp': message.get('timestamp'),
                'ask_id': ask_id,
                'credentials': self.get_credentials()
            }
            token = self.create_token(trading_request, algorithm='RS256')
            # End session after ask is complete
            self.end_ask(ask_id)
            return {
                'status': 'success',
                'message': 'Trading request created',
                'request': trading_request,
                'token': token
            }
        return {
            'status': 'error',
            'message': 'Invalid message type'
        }
    
    def create_trading_request(self, goals: Dict[str, Any], constraints: Dict[str, Any], ask_id: str) -> Dict[str, Any]:
        """Create a new trading request with specified goals and constraints, including ask_id."""
        request = {
            'type': 'trading_request',
            'goals': goals,
            'constraints': constraints,
            'timestamp': datetime.utcnow().isoformat(),
            'ask_id': ask_id,
            'credentials': self.get_credentials()
        }
        token = self.create_token(request, algorithm='RS256')
        return {
            'request': request,
            'token': token
        } 