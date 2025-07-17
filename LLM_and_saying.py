import os
from pydantic_ai import Agent, RunContext, BinaryContent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.providers.openrouter import OpenRouterProvider
from dotenv import load_dotenv, find_dotenv
from typing import Any
import logfire
import time


# logfire.configure(console=False)
# logfire.instrument_pydantic_ai()

load_dotenv(find_dotenv())

class LLMAndSaying:
    def __init__(self, motion_service, video_service, video_handle, prompt_name='system_message', language='Polski'):
        """Initialize the agent with system prompt and movement tools"""

        self.motion_service = motion_service
        self.video_service = video_service
        self.video_handle = video_handle

        self.is_idle = True  # Flag to track if the robot is idle
        self.message_history = []  # Conversation history management
        self.system_prompt = self._load_system_message(prompt_name, language)
        self.openrouter_model = OpenAIModel(
            'openai/gpt-4.1',
            #'meta-llama/llama-4-maverick',
            #'deepseek/deepseek-chat-v3-0324',
            provider=OpenRouterProvider(api_key=os.getenv('OPENROUTER_API_KEY')),
        )
        self.agent = Agent(
            self.openrouter_model,
            system_prompt=self.system_prompt
        )
        self.agent.tool(self._move_forward_tool(motion_service))
        self.agent.tool(self._turn_robot_tool(motion_service))
        self.agent.tool(self._look_around_tool(motion_service, video_service, video_handle))
        self.agent.tool(self.task_finished_tool(motion_service))

    async def generate_say_execute_response(self, user_input, speech_service, sound_module, is_idle):
        full_response = ""
        sentence_buffer = ""
        self.is_idle = is_idle  # Update idle state based on the input
        try:
            async with self.agent.run_stream(user_input, message_history=self.message_history) as result:
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
                    if token.endswith('.') or token.endswith('!') or token.endswith('?'):# or token.endswith(','):
                        if sentence_buffer.strip():
                            speech_service.say(sentence_buffer.strip())
                            sentence_buffer = ""

                # Speak final sentence if any
                if sentence_buffer.strip():
                    speech_service.say(sentence_buffer.strip())

                # Update message history with new messages
                self.message_history.extend(result.new_messages())
                return self.is_idle
        finally:
            # Always restore listening, even if the task was cancelled
            sound_module.setListening()

    def reset_conversation(self):
        """Reset conversation history for a new task"""
        self.message_history = []

    def trim_history(self, messages, max_size=6):
        """Keep system message + last max_size conversation messages"""
        if len(messages) <= max_size:
            return messages

        # Zachowaj pierwszą wiadomość (zawiera system prompt) + ostatnie (max_size-1) wiadomości
        return [messages[0]] + messages[-(max_size - 1):]

    def _load_system_message(self, prompt_name, language):
        """Load system message from .prompt file"""
        with open(f'prompts/{prompt_name}.prompt', 'r', encoding='utf-8') as f:
            system_prompt = f.read().strip()
        system_prompt += f"\n\nRespond in {language}."
        return system_prompt

    def _move_forward_tool(self, motion_service):
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

    def _turn_robot_tool(self, motion_service):
        """Create turn robot tool for the agent"""
        def turn_robot(ctx: RunContext[Any], degrees: float):
            """Turn the robot by specified angle in degrees (positive = left, negative = right)"""
            print(f"Turning {degrees} degrees")
            # Convert degrees to radians
            radians = degrees * 0.01745
            motion_service.wakeUp()
            motion_service.moveTo(0.0, 0.0, radians)

        return turn_robot

    def _look_around_tool(self, motion_service, video_service, video_handle):
        """Create look around tool for the agent"""
        def look_around(ctx: RunContext[Any]):
            """Look around yourself to understand envinronment. Use that tool when you can't see the thing you are looking for"""
            from motion import turnHead
            from camera import take_picture

            print("Looking around - taking 5 photos at different angles")

            photos = []
            angles = [-120, -60, 0, 60, 120]

            for angle in angles:
                turnHead(motion_service, angle)
                time.sleep(1)  # Wait for head to move

                # Take picture with appropriate center angle for markers
                photo_bytes = take_picture(video_service, video_handle, center_angle=angle)
                photo_content = BinaryContent(data=photo_bytes, media_type='image/jpeg')
                photos.append(photo_content)

            # Return head to center position
            print("Returning head to center position")
            turnHead(motion_service, 0)

            return photos
        
        return look_around
    
    def task_finished_tool(self, motion_service):
        """Create task finished tool for the agent"""
        def task_finished(ctx: RunContext[Any]):
            """Signal that the task given you by a human is finished or can't be done."""
            print("Task finished - returning to idle state")
            self.is_idle = True
        return task_finished
