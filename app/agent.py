import os
from typing import List, Dict
from agents import Agent, Runner

# Simple agent setup
chat_agent = Agent(
    name="Assistant",
    instructions="You are a helpful AI assistant. Answer clearly and concisely. You have access to previous conversation history.",
    model="gpt-4o-mini"
)

def run_agent_stream(messages: List[Dict[str, str]]):
    """Run agent with streaming and conversation history.
    
    Args:
        messages: List of conversation messages in format:
                 [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}, ...]
    """
    # For OpenAI Agents SDK, we need to pass the conversation in the right format
    # The latest message is the current user input
    if not messages:
        raise ValueError("At least one message is required")
    
    # Extract just the latest message as input, but the agent should have access to history
    latest_message = messages[-1]["content"]
    
    # TODO: Check if OpenAI Agents SDK supports conversation history
    # For now, we concatenate the conversation as context
    conversation_context = "\n".join([
        f"{msg['role'].title()}: {msg['content']}" 
        for msg in messages[:-1]  # All except the last one
    ])
    
    if conversation_context:
        input_with_context = f"Previous conversation:\n{conversation_context}\n\nUser: {latest_message}"
    else:
        input_with_context = latest_message
    
    return Runner.run_streamed(chat_agent, input=input_with_context)

