"""
Vapi Voice Agent Setup and Management
Handles voice agent creation, configuration, and telephony
"""

import os
import json
import requests
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

load_dotenv()


class VapiVoiceAgent:
    """Main class for Vapi voice agent management"""
    
    def __init__(self):
        self.api_key = os.getenv("VAPI_API_KEY")
        self.base_url = "https://api.vapi.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load Vapi configuration from JSON file"""
        config_path = os.path.join(os.path.dirname(__file__), "../config/vapi_config.json")
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Replace environment variables in config
        config_str = json.dumps(config)
        for key, value in os.environ.items():
            config_str = config_str.replace(f"{{{{{key}}}}}", value)
        
        return json.loads(config_str)
    
    def create_assistant(self, custom_config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a new Vapi assistant
        
        Args:
            custom_config: Optional custom configuration to override defaults
            
        Returns:
            Assistant creation response with assistant_id
        """
        config = self.config["assistant"].copy()
        if custom_config:
            config.update(custom_config)
        
        try:
            response = requests.post(
                f"{self.base_url}/assistant",
                headers=self.headers,
                json=config
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ Assistant created successfully: {result.get('id')}")
            return result
        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating assistant: {e}")
            raise
    
    def update_assistant(self, assistant_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing assistant
        
        Args:
            assistant_id: ID of the assistant to update
            updates: Dictionary of fields to update
            
        Returns:
            Updated assistant data
        """
        try:
            response = requests.patch(
                f"{self.base_url}/assistant/{assistant_id}",
                headers=self.headers,
                json=updates
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ Assistant updated successfully")
            return result
        except requests.exceptions.RequestException as e:
            print(f"❌ Error updating assistant: {e}")
            raise
    
    def get_assistant(self, assistant_id: str) -> Dict[str, Any]:
        """Get assistant details"""
        try:
            response = requests.get(
                f"{self.base_url}/assistant/{assistant_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching assistant: {e}")
            raise
    
    def list_assistants(self) -> List[Dict[str, Any]]:
        """List all assistants"""
        try:
            response = requests.get(
                f"{self.base_url}/assistant",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error listing assistants: {e}")
            raise
    
    def delete_assistant(self, assistant_id: str) -> bool:
        """Delete an assistant"""
        try:
            response = requests.delete(
                f"{self.base_url}/assistant/{assistant_id}",
                headers=self.headers
            )
            response.raise_for_status()
            print(f"✅ Assistant deleted successfully")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error deleting assistant: {e}")
            raise
    
    def create_phone_call(
        self, 
        phone_number: str, 
        assistant_id: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Initiate an outbound phone call
        
        Args:
            phone_number: Phone number to call (E.164 format)
            assistant_id: Assistant to use for the call
            metadata: Optional metadata to attach to the call
            
        Returns:
            Call creation response
        """
        payload = {
            "phoneNumber": phone_number,
            "assistantId": assistant_id or os.getenv("VAPI_ASSISTANT_ID"),
        }
        
        if metadata:
            payload["metadata"] = metadata
        
        try:
            response = requests.post(
                f"{self.base_url}/call/phone",
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ Call initiated: {result.get('id')}")
            return result
        except requests.exceptions.RequestException as e:
            print(f"❌ Error creating phone call: {e}")
            raise
    
    def get_call(self, call_id: str) -> Dict[str, Any]:
        """Get call details"""
        try:
            response = requests.get(
                f"{self.base_url}/call/{call_id}",
                headers=self.headers
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching call: {e}")
            raise
    
    def list_calls(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List recent calls"""
        try:
            response = requests.get(
                f"{self.base_url}/call",
                headers=self.headers,
                params={"limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error listing calls: {e}")
            raise
    
    def end_call(self, call_id: str) -> bool:
        """End an active call"""
        try:
            response = requests.delete(
                f"{self.base_url}/call/{call_id}",
                headers=self.headers
            )
            response.raise_for_status()
            print(f"✅ Call ended successfully")
            return True
        except requests.exceptions.RequestException as e:
            print(f"❌ Error ending call: {e}")
            raise
    
    def update_call_language(self, call_id: str, language: str) -> Dict[str, Any]:
        """
        Update the language during an active call
        
        Args:
            call_id: ID of the active call
            language: Language code (en, hi, kn)
        """
        voice_map = {
            "en": "en-IN-Wavenet-A",
            "hi": "hi-IN-Wavenet-A",
            "kn": "kn-IN-Wavenet-A"
        }
        
        try:
            response = requests.patch(
                f"{self.base_url}/call/{call_id}",
                headers=self.headers,
                json={
                    "voice": {
                        "voiceId": voice_map.get(language, "en-IN-Wavenet-A")
                    }
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error updating call language: {e}")
            raise
    
    def get_analytics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get analytics for calls within a date range
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
        """
        try:
            response = requests.get(
                f"{self.base_url}/analytics",
                headers=self.headers,
                params={
                    "startDate": start_date,
                    "endDate": end_date
                }
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching analytics: {e}")
            raise


def setup_voice_agent():
    """Setup and configure the Vapi voice agent"""
    agent = VapiVoiceAgent()
    
    # Check if assistant already exists
    assistant_id = os.getenv("VAPI_ASSISTANT_ID")
    
    if assistant_id:
        print(f"📞 Using existing assistant: {assistant_id}")
        assistant = agent.get_assistant(assistant_id)
        print(f"✅ Assistant loaded: {assistant.get('name')}")
    else:
        print("📞 Creating new assistant...")
        assistant = agent.create_assistant()
        print(f"✅ New assistant created with ID: {assistant.get('id')}")
        print(f"⚠️  Add this to your .env file: VAPI_ASSISTANT_ID={assistant.get('id')}")
    
    return agent, assistant


if __name__ == "__main__":
    # Setup the voice agent
    agent, assistant = setup_voice_agent()
    
    # Display configuration
    print("\n" + "="*60)
    print("🎙️  VAPI VOICE AGENT CONFIGURED")
    print("="*60)
    print(f"Assistant ID: {assistant.get('id')}")
    print(f"Assistant Name: {assistant.get('name')}")
    print(f"Voice: {assistant.get('voice', {}).get('voiceId')}")
    print(f"Model: {assistant.get('model', {}).get('model')}")
    print("="*60)
    
    # Test outbound call (uncomment to test)
    # test_number = input("\nEnter phone number to test (E.164 format, e.g., +919876543210): ")
    # if test_number:
    #     call = agent.create_phone_call(test_number, assistant.get('id'))
    #     print(f"Test call initiated: {call.get('id')}")

