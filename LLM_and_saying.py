import os
from pydantic_ai import Agent, RunContext, BinaryContent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
from typing import Any
import time
import cv2
from rpi_client import RPiController
from motion import grabGun, lowerGun, turnHead
from camera import draw_gun_camera_crosshair
import logfire
import requests



# logfire.configure(console=False)
# logfire.instrument_pydantic_ai()

load_dotenv(find_dotenv())


class Corrections(BaseModel):
    vertical_correction: float  # stopnie, + = do góry, – = w dół
    horizontal_correction: float  # stopnie, + = w lewo, – = w prawo


class LLMAndSaying:
    def __init__(self, motion_service, video_service, video_handle, sound_module, speech_service, prompt_name='system_message_shooting', language='Polski'):
        """Initialize the agent with system prompt and movement tools"""

        self.motion_service = motion_service
        self.video_service = video_service
        self.video_handle = video_handle

        self.is_idle = True  # Flag to track if the robot is idle
        self.message_history = []  # Conversation history management
        self.system_prompt = self._load_system_message(prompt_name, language)
        self.openrouter_model = OpenAIModel(
            #'openai/gpt-4.1',
            #'meta-llama/llama-4-maverick',
            'google/gemini-2.5-pro',
            #'anthropic/claude-sonnet-4'
            provider=OpenRouterProvider(api_key=os.getenv('OPENROUTER_API_KEY')),
        )
        self.rpi_controller = RPiController()
        self.agent = Agent(
            self.openrouter_model,
            system_prompt=self.system_prompt
        )
        self.agent.tool(self._move_forward_tool(motion_service))
        self.agent.tool(self._turn_robot_tool(motion_service))
        self.agent.tool(self._look_around_tool(motion_service, video_service, video_handle))
        #self.agent.tool(self._say_tool(sound_module, speech_service))
        #self.agent.tool(self._look_forward_tool(motion_service, video_service, video_handle))
        #self.agent.tool(self._manipulate_hand_tool(motion_service))
        self.agent.tool(self._shoot_tool(motion_service))
        self.agent.tool(self.task_finished_tool())
        self.shooter_llm = Agent(self.openrouter_model, output_type=Corrections)

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
            # print("Waking start")
            motion_service.moveTo(meters, 0.0, 0.0)
            # print("Waking end")

        return move_forward

    def _turn_robot_tool(self, motion_service):
        """Create turn robot tool for the agent"""
        def turn_robot(ctx: RunContext[Any], degrees: float):
            """
            Turn the robot by specified angle in degrees (positive = left, negative = right).
            param degrees: angle to turn. Hint: angle value you see on the photo under the target is the value you need to provide here (keep sign as well).
            """
            print(f"Turning {degrees} degrees")

            print(motion_service.getExternalCollisionProtectionEnabled("Arms"))
            # add additional 7 degrees with same vector for calm friction
            # if abs(degrees) <= 20:
            #     degrees = degrees + 7 if degrees > 0 else degrees - 7
            radians = degrees * 0.01745
            motion_service.stopMove()
            motion_service.moveTo(0.0, 0.0, radians)
            motion_service.waitUntilMoveIsFinished()
            turnHead(motion_service, 0)  # zeroing head position

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

    def _shoot_tool(self, motion_service):
        """Create tool for the agent"""
        def shoot(ctx: RunContext[Any], vertical_angle: float, target_name: str):
            """
            Shoot. Calling that tool shoots using airsoft gun to the front of you.
            Ensure object you want to shoot is exactly in front of you (on 0 deg).
            If not exactly at 0 deg, rotate yourself first.

            :param vertical_angle: angle of vertical target in degrees (positive = up, negative = down)
            :param target_name: name and short description of target
            """
            print(f"[SHOOT TOOL] Shooting: {target_name}, Initial vertical angle: {vertical_angle} deg")
            grabGun(motion_service, vertical_angle, 0)
            motion_service.waitUntilMoveIsFinished()
            # Take photo from gun camera
            gun_photo = self.rpi_controller.capture_image()

            gun_photo = cv2.resize(gun_photo, (int(gun_photo.shape[1]/4), int(gun_photo.shape[0]/4))) # lower resolution to fit llm. ToDo: Make on RPi side.
            # Apply crosshair grid to gun camera image
            gun_photo_with_grid = draw_gun_camera_crosshair(gun_photo)
            # make resolution lesser
            # write to file
            cv2.imwrite("gun_camera_with_grid.png", gun_photo_with_grid)


            # Convert processed image to bytes for LLM
            _, buffer = cv2.imencode('.jpg', gun_photo_with_grid, [cv2.IMWRITE_JPEG_QUALITY, 90])
            photo_bytes = buffer.tobytes()
            photo_content = BinaryContent(data=photo_bytes, media_type='image/jpeg')

            # Prepare detailed input for LLM
            llm_prompt = f"""Analyze the gun camera image to determine shooting corrections for target: {target_name}.
            
            Aim in the very middle of the target. You need to provide:
            1. vertical_correction: degrees to adjust up (positive) or down (negative) to hit the target
            2. horizontal_correction: degrees to adjust left (positive) or right (negative) to hit the target"""

            # Get corrections from LLM (single call with structured output)
            corrections = self.shooter_llm.run_sync(
                [llm_prompt, photo_content],
            )

            # Apply corrections - vertical starts from 0, horizontal adds to initial correction
            final_vertical_correction = corrections.output.vertical_correction
            final_horizontal_correction = vertical_angle + corrections.output.horizontal_correction
            
            print(f"[SHOOT TOOL] shoot corrections. Vertical: {corrections.output.vertical_correction} deg, Horizontal: {corrections.output.horizontal_correction} deg")

            grabGun(motion_service, final_vertical_correction, final_horizontal_correction)
            time.sleep(1)  # Wait for hand ro raise
            self.rpi_controller.fire()
            time.sleep(1)    # Wait for gun to shoot
            time.sleep(10) # for barrel kierunek analisys
            lowerGun(motion_service)

            motion_service.waitUntilMoveIsFinished()

            return f"Shot fired at {target_name} with corrections - V: {corrections['vertical_correction']}°, H: {corrections['horizontal_correction']}°"
        
        return shoot

    def _say_tool(self, sound_module, speech_service):
        """Create say tool for the agent"""
        async def say(ctx: RunContext[Any], message: str):
            """Say something to the human. Use that tool when you want to tell something to human."""
            print(f"Saying: {message}")
            full_response = ""
            sentence_buffer = ""
            try:
                async with self.agent.run_stream(message, message_history=self.message_history) as result:
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
                        if token.endswith('.') or token.endswith('!') or token.endswith('?'):  # or token.endswith(','):
                            if sentence_buffer.strip():
                                speech_service.say(sentence_buffer.strip())
                                sentence_buffer = ""

                    # Speak final sentence if any
                    if sentence_buffer.strip():
                        speech_service.say(sentence_buffer.strip())

                    # Update message history with new messages
                    self.message_history.extend(result.new_messages())
            finally:
                # Always restore listening, even if the task was cancelled
                sound_module.setListening()

        return say

    def task_finished_tool(self):
        """Create task finished tool for the agent"""
        def task_finished(ctx: RunContext[Any], reason: str):
            """Signal that the task given you by a human is finished or can't be done. Write short reason why you think task is finished."""
            print(f"Task finished - returning to idle state. Reason: '{reason}'")
            self.is_idle = True
        return task_finished
