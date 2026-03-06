import os
from agents import Agent, Runner

# Simple agent setup
chat_agent = Agent(
    name="Assistant",
    instructions="You are a helpful AI assistant. Answer clearly and concisely.",
    model="gpt-4o-mini"
)

def run_agent_stream(message: str):
    """Run agent with streaming."""
    return Runner.run_streamed(chat_agent, input=message)

