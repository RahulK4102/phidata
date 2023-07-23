from typing import Optional, Any
from pydantic import BaseModel


class Message(BaseModel):
    """Pydantic model for holding LLM messages"""

    # The role of the messages author.
    # One of system, user, assistant, or function.
    role: str
    # The contents of the message. content is required for all messages,
    # and may be null for assistant messages with function calls.
    content: str
    # The name of the author of this message. name is required if role is function,
    # and it should be the name of the function whose response is in the content.
    # May contain a-z, A-Z, 0-9, and underscores, with a maximum length of 64 characters.
    name: Optional[str] = None
    # The name and arguments of a function that should be called, as generated by the model.
    function_call: Optional[Any] = None


class ConversationRow(BaseModel):
    """Pydanctic model for holding LLM conversations"""

    id: Optional[int] = None
    # The user ID of the user who is participating in this conversation.
    user_id: str
    # The persona of the user who is participating in this conversation.
    user_persona: Optional[str] = None
    # The data of the user who is participating in this conversation.
    user_data: Optional[Any] = None
    # The chat history of the user who is participating in this conversation.
    user_chat_history: Optional[Any] = None
    # The chat history of the LLM who is participating in this conversation.
    llm_chat_history: Optional[Any] = None
    # The usage data of the user who is participating in this conversation.
    usage_data: Optional[Any] = None
    # True if this conversation is active.
    is_active: bool
    # The timestamp of when this conversation was created.
    created_at: Optional[str] = None
    # The timestamp of when this conversation was last updated.
    updated_at: Optional[str] = None
