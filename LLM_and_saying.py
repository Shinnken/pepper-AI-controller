import os
from pydantic_ai import Agent, RunContext, BinaryContent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider
from dotenv import load_dotenv, find_dotenv
from typing import Any
import logfire
import time


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
    'openai/gpt-4.1-mini',
    #'meta-llama/llama-3.3-70b-instruct',
    provider=OpenRouterProvider(api_key=os.getenv('OPENROUTER_API_KEY')),
)


async def generate_and_say_response(agent, user_input, message_history, speech_service, sound_module):
    full_response = ""
    sentence_buffer = ""
    # Generating and saying response
    async with agent.run_stream(user_input, message_history=message_history) as result:
        # tts.say(random.choice(animations))
        async for token in result.stream_text(delta=True):
            # Check if adding this token would exceed 1000 characters
            if len(full_response) + len(token) > 2000:
                break

            print(token, end='', flush=True)
            full_response += token
            sentence_buffer += token

            # Do not listen while talking
            if sound_module.is_listening:
                sound_module.setNotListening()
            
            # If token ends with sentence delimiter, speak the buffered sentence
            if token.endswith('.') or token.endswith('!') or token.endswith('?') or token.endswith(','):
                if sentence_buffer.strip():
                    speech_service.say(sentence_buffer.strip())
                    sentence_buffer = ""
        
        # Speak final sentence if any
        if sentence_buffer.strip():
            speech_service.say(sentence_buffer.strip())

        # set listening back
        sound_module.setListening()

        return result.new_messages()


def load_system_message(prompt_name='system_message', language='Polski'):
    """Load system message from .prompt file"""
    with open(f'prompts/{prompt_name}.prompt', 'r', encoding='utf-8') as f:
        system_prompt = f.read().strip()
    system_prompt += f"\n\nRespond in {language}."
    return system_prompt


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

        if meters > 2:
            meters = 2
        elif meters < 0:
            meters = 0

        print(f"Moving forward {meters} meters")
        motion_service.wakeUp()
        motion_service.moveTo(meters, 0.0, 0.0)

    return move_forward


def turn_robot_tool(motion_service):
    """Create turn robot tool for the agent"""
    def turn_robot(ctx: RunContext[Any], degrees: float):
        """Turn the robot by specified angle in degrees (positive = left, negative = right)"""
        print(f"Turning {degrees} degrees")
        # Convert degrees to radians
        radians = degrees * 0.017453
        motion_service.wakeUp()
        motion_service.moveTo(0.0, 0.0, radians)

    return turn_robot

def look_around_tool(motion_service, video_service, video_handle):
    """Create look around tool for the agent"""
    def look_around(ctx: RunContext[Any]):
        """Look around yourself to understand envinronment. Use that tool when you can't see the thing you are looking for"""
        from motion import turnHead
        from camera import take_picture
        
        print("Looking around - taking 3 photos at different angles")
        
        photos = []
        angles = [120, -120, 0]
        
        for angle in angles:
            turnHead(motion_service, angle)
            time.sleep(1)  # Wait for head to move
            
            # Take picture with appropriate center angle for markers
            photo_bytes = take_picture(video_service, video_handle, center_angle=angle)
            photo_content = BinaryContent(data=photo_bytes, media_type='image/jpeg')
            photos.append(photo_content)
        # placing middle photo (last taken) in the middle of the list
        photos[1], photos[2] = photos[2], photos[1]
        
        # Return head to center position
        print("Returning head to center position")
        turnHead(motion_service, 0)
        
        return photos
    
    return look_around




def init_agent(motion_service, video_service, video_handle, prompt_name='system_message', language='Polski'):
    """Initialize the agent with system prompt and movement tools"""
    # Load system prompt from file
    system_prompt = load_system_message(prompt_name=prompt_name, language=language)

    # Create agent with OpenRouter model
    agent = Agent(
        openrouter_model,
        system_prompt=system_prompt
    )

    # Add movement tools
    agent.tool(move_forward_tool(motion_service))
    agent.tool(turn_robot_tool(motion_service))
    agent.tool(look_around_tool(motion_service, video_service, video_handle))

    return agent
