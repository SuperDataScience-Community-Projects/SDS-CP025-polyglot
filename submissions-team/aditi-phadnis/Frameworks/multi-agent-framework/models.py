import uuid
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel, Field
from langchain.memory.chat_memory import BaseChatMemory
from langchain.memory import ConversationBufferMemory


class UserProfile(BaseModel):
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    target_language: str = "Spanish"
    difficulty_level: str = "Beginner"
    learning_focus: str = "Vocabulary"
    strengths: List[str] = []
    weaknesses: List[str] = []
    conversation_history: List[Dict] = []
    exercise_history: List[Dict] = []
    feedback_history: List[Dict] = []

class MultiInputMemory(ConversationBufferMemory):
    """Memory class that handles multiple input keys and combines them."""
    
    def __init__(self, 
                memory_key: str = "chat_history", 
                primary_input_key: str = "input",  
                include_keys: List[str] = None, 
                output_key: str = "output", 
                return_messages: bool = False):
        super().__init__(memory_key=memory_key, 
                         output_key=output_key, 
                         return_messages=return_messages)
        
        object.__setattr__(self, "primary_input_key", primary_input_key)
        object.__setattr__(self, "include_keys", include_keys or [])

        self.chat_memory.messages = []
    
    def memory_variables(self) -> List[str]:
        """Return the memory variables."""
        return [self.memory_key] + self.include_keys

    def _get_input_output(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> Tuple[str, str]:
        """Extract and format input and output from chain inputs and outputs."""
        primary_input = inputs.get(self.primary_input_key, "")
        additional_info = ""
        
        if self.include_keys:
            additional_parts = [f"{key}: {inputs[key]}" for key in self.include_keys if key in inputs]
            additional_info = f" [{', '.join(additional_parts)}]" if additional_parts else ""
        
        input_str = f"{primary_input}{additional_info}"
        output_str = outputs.get(self.output_key, "")
        return input_str, output_str
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Return history in format appropriate for the prompt."""
        return {self.memory_key: self.chat_memory.messages}
