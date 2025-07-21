import os
from pydantic_ai import Agent, RunContext, BinaryContent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from dotenv import load_dotenv, find_dotenv
from typing import Any
import time
import cv2
from vla_and_vision.metal_bottle_detector import target_and_shoot_bottle
from motion import grabGun
import logfire


logfire.configure(console=False)
logfire.instrument_pydantic_ai()

load_dotenv(find_dotenv())

class LLMAndSaying:
    def __init__(self, motion_service, video_service, video_handle, prompt_name='system_message_shooting', language='Polski'):
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
        self.agent.tool(self._say_tool())
        #self.agent.tool(self._look_forward_tool(motion_service, video_service, video_handle))
        #self.agent.tool(self._manipulate_hand_tool(motion_service))
        self.agent.tool(self._shoot_tool(motion_service, video_service, video_handle))
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
            # motion_service.wakeUp()
            # print("Waking start")
            motion_service.moveTo(meters, 0.0, 0.0)
            # print("Waking end")

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
            # print("Turning end")

        return turn_robot

    def _look_around_tool(self, motion_service, video_service, video_handle):
        """Create look around tool for the agent"""
        def look_around(ctx: RunContext[Any]):
            """Look around yourself to understand envinronment. Use that tool when you can't see the thing you are looking for"""
            from motion import turnHead
            from camera import take_picture

            print("Looking around - taking 5 photos at different angles")

            photos = []
            angles = [-120, -60, 0, 120, 60]

            for angle in angles:
                turnHead(motion_service, angle)
                time.sleep(0.2)  # Wait for head to move

                # Get raw NumPy image array
                image_buffer = take_picture(video_service, video_handle, center_angle=angle)
                
                # Encode the image to JPEG, then convert to bytes for the LLM
                _, buffer = cv2.imencode('.jpg', image_buffer, [cv2.IMWRITE_JPEG_QUALITY, 70])
                photo_bytes = buffer.tobytes()
                photo_content = BinaryContent(data=photo_bytes, media_type='image/jpeg')
                photos.append(photo_content)

                # save photo buffer to file (use opencv functions), place angle in the filename
                with open(f"pepper_image_{angle}.jpg", 'wb') as f:
                    f.write(buffer)


            # Return head to center position
            print("Returning head to center position")
            turnHead(motion_service, 0)

            return photos
        
        return look_around
    
    def _look_forward_tool(self, motion_service, video_service, video_handle):
        """Create look forward tool for the agent"""
        def look_forward(ctx: RunContext[Any]):
            """Take a photo of what you currently see in front of you to analyze the environment"""
            from camera import take_picture
            
            print("Taking photo of what's in front")

            # Get raw NumPy image array
            image_buffer = take_picture(video_service, video_handle, center_angle=0)


            # Encode the image to JPEG, then convert to bytes for the LLM
            _, buffer = cv2.imencode('.jpg', image_buffer, [cv2.IMWRITE_JPEG_QUALITY, 70])
            photo_bytes = buffer.tobytes()
            photo_content = BinaryContent(data=photo_bytes, media_type='image/jpeg')

            return photo_content
        
        return look_forward

    def _manipulate_hand_tool(self, motion_service):
        """Create hand manipulation tool for the agent"""
        def manipulate_robot_hand(ctx: RunContext[Any], hand: str, action: str):
            """
            Manipulate the robot's hand.
            :param hand: which hand to manipulate, either "left" or "right".
            :param action: what to do with the hand, either "open" or "close".
            """
            print(f"Manipulating {hand} hand to {action}")
            hand_name = "RHand" if hand.lower() == "right" else "LHand"

            if action.lower() == "open":
                motion_service.openHand(hand_name)
            else:  # "close"
                motion_service.closeHand(hand_name)

            return f"Successfully {action}ed {hand} hand."

        return manipulate_robot_hand

    def _shoot_tool(self, motion_service, video_service, video_handle):
        """Create tool for the agent"""
        def shoot(ctx: RunContext[Any], vertical_angle: float):
            """
            Shoot. Calling that tool shoots using airsoft gun to the front of you.
            Ensure object you want to shoot is exactly in front of you (on 0 deg).
            If not exacly at 0 deg, rotate yourself first.

            :param vertical_angle: angle of vertical angle in degrees (positive = up, negative = down)
            """
            print("Executing shoot tool")
            grabGun(motion_service, vertical_angle)
            result = target_and_shoot_bottle(video_service, video_handle, motion_service)
            return result
        
        return shoot

    def _say_tool(self):
        """Create say tool for the agent"""
        def say(ctx: RunContext[Any], message: str):
            """Say something to the human. Use that tool when you want to tell something to human."""
            print(f"Say: '{message}'")

        return say

    def task_finished_tool(self, motion_service):
        """Create task finished tool for the agent"""
        def task_finished(ctx: RunContext[Any], reason: str):
            """Signal that the task given you by a human is finished or can't be done. Write short reason why you think task is finished."""
            print(f"Task finished - returning to idle state. Reason: '{reason}'")
            self.is_idle = True
        return task_finished
