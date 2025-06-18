import os
from pydantic_ai import Agent
from pydantic_ai import RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider
from dotenv import load_dotenv, find_dotenv
from typing import Any
import logfire


logfire.configure(console=False)
logfire.instrument_pydantic_ai()

load_dotenv(find_dotenv())

ollama_model = OpenAIModel(
        model_name='SpeakLeash/bielik-11b-v2.1-instruct:Q8_0',
        #model_name='SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0',
        #provider=OpenAIProvider(base_url='http://localhost:11434/v1')
        provider=OpenAIProvider(base_url='https://intent-possum-hardy.ngrok-free.app/v1')
    )

openrouter_model = OpenAIModel(
    #'qwen/qwen3-32b',
    'meta-llama/llama-3.3-70b-instruct',
    provider=OpenRouterProvider(api_key=os.getenv('OPENROUTER_API_KEY')),
)


async def generate_and_say_response(agent, user_input, message_history, speech_service):
    full_response = ""
    word_buffer = ""
    # Generating and saying response
    async with agent.run_stream(user_input, message_history=message_history) as result:
        # tts.say(random.choice(animations))
        async for token in result.stream_text(delta=True):
            # Check if adding this token would exceed 1000 characters
            if len(full_response) + len(token) > 2000:
                break

            print(token, end='', flush=True)
            full_response += token

            # If token starts with space and buffer has more than 1 character, speak it
            if token.startswith(' ') and len(word_buffer.strip()) > 1:
                speech_service.say(word_buffer.strip())
                word_buffer = token[1:]  # Start new word without space
            else:
                word_buffer += token
        # Speak final word if any
        if word_buffer.strip():
            pass
            speech_service.say(word_buffer.strip())

        return result.new_messages()


def load_system_message(prompt_name='system_message'):
    """Load system message from .prompt file"""
    with open(f'prompts/{prompt_name}.prompt', 'r', encoding='utf-8') as f:
        return f.read().strip()


def trim_history(messages, max_size=6):
    """Keep system message + last max_size conversation messages"""
    if len(messages) <= max_size:
        return messages

    # Zachowaj pierwszą wiadomość (zawiera system prompt) + ostatnie (max_size-1) wiadomości
    return [messages[0]] + messages[-(max_size - 1):]


def move_forward_tool(motion_service):
    """Create move forward tool for the agent"""
    def move_forward(ctx: RunContext[Any], meters: float):
        """Move the robot forward by specified meters (max 2 meters)"""

        motion_service.wakeUp()
        if meters > 2:
            meters = 2
        elif meters < 0:
            meters = 0

        print(f"Moving forward {meters} meters")
        motion_service.moveTo(meters, 0.0, 0.0)

    return move_forward


def turn_robot_tool(motion_service):
    """Create turn robot tool for the agent"""
    def turn_robot(ctx: RunContext[Any], degrees: float):
        """Turn the robot by specified angle in degrees (positive = left, negative = right)"""
        # Convert degrees to radians
        radians = degrees * 0.017453
        motion_service.moveTo(0.0, 0.0, radians)

    return turn_robot


def init_agent(motion_service, prompt_name='system_message'):
    """Initialize the agent with system prompt and movement tools"""
    # Load system prompt from file
    system_prompt = load_system_message(prompt_name)

    # Create agent with OpenRouter model
    agent = Agent(
        openrouter_model,
        system_prompt=system_prompt
    )
    
    # Add movement tools
    #agent.tool(move_forward_tool(motion_service))
    #agent.tool(turn_robot_tool(motion_service))

    return agent

