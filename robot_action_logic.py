from pydantic_ai import BinaryContent
from camera import take_picture
from LLM_and_saying import LLMAndSaying




class RobotActionHandler:
    def __init__(self, motion_service, video_service, vid_handle, sound_module, tts, language):
        self.sound_module = sound_module
        self.tts = tts
        self.video_service = video_service
        self.vid_handle = vid_handle
        # Initialize LLM agent here
        self.llm_agent = LLMAndSaying(motion_service, video_service, vid_handle, language=language)
        self.is_idle = True

    async def run_task(self, initial_command):
        """Execute complete robot task from initial command until completion"""
        print(f"[ROBOT_TASK] Starting robot task with initial command: '{initial_command}'")
        self.llm_agent.reset_conversation()  # Reset conversation for new task
        self.is_idle = False
        current_command = initial_command

        print("[ROBOT_TASK] Entering task execution loop...")
        while not self.is_idle:
            print(f"[ROBOT_TASK] Executing action step with command: '{current_command}'")
            self.is_idle = await self._execute_single_step(current_command)
            print(f"[ROBOT_TASK] Action step completed. Is idle: {self.is_idle}")

            # Check for new commands during task execution
            if not self.is_idle:
                if self.sound_module.stt_output is not None:
                    current_command = self.sound_module.stt_output
                    self.sound_module.stt_output = None
                    print(f"[ROBOT_TASK] Got new command during task: '{current_command}' - incorporating into task")
                else:
                    current_command = ""  # Continue working
                    print("[ROBOT_TASK] No new command, continuing task execution...")

        print(f"[ROBOT_TASK] Task completed successfully, exiting loop")

    async def _execute_single_step(self, user_command):
        """Execute a single perception-decision-action cycle"""
        # Capture environment
        camera_view_bytes = take_picture(self.video_service, self.vid_handle)
        image_content = BinaryContent(data=camera_view_bytes, media_type='image/jpeg')

        # Prepare multimodal input
        user_input = [
            f"Human voice command: '{user_command}'.\n\nThat's what you see on the front:" if user_command else "That's what you see on the front:",
            image_content
        ]

        # Get LLM response and execute actions
        is_idle = await self.llm_agent.generate_say_execute_response(
            user_input,
            self.tts,
            self.sound_module,
            is_idle=self.is_idle
        )
        print()  # Add newline after streaming

        return is_idle
