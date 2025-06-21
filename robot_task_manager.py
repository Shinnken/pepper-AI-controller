import asyncio
from pydantic_ai import BinaryContent
from camera import take_picture


class RobotTaskManager:
    """Manages robot task execution without polling loops"""
    
    def __init__(self, sound_module, llm_agent, tts, video_service, vid_handle):
        self.sound_module = sound_module
        self.llm_agent = llm_agent
        self.tts = tts
        self.video_service = video_service
        self.vid_handle = vid_handle
        self.current_task = None
        self.is_idle = True
        
    async def start_new_task(self, command: str):
        """Start a new robot task"""
        if self.current_task and not self.current_task.done():
            print("[TASK_MGR] Warning: Starting new task while another is active")
            
        print(f"[TASK_MGR] Starting new task: '{command}'")
        self.current_task = asyncio.create_task(self._execute_task(command))
        return self.current_task
        
    async def _execute_task(self, initial_command: str):
        """Execute complete task until finished"""
        message_history = []
        self.is_idle = False
        user_text = initial_command
        
        while not self.is_idle:
            print(f"[TASK] Step: '{user_text}'")
            
            # Take picture and prepare input
            camera_view_bytes = take_picture(self.video_service, self.vid_handle)
            image_content = BinaryContent(data=camera_view_bytes, media_type='image/jpeg')
            
            user_input = [
                f"Human voice command: '{user_text}'.\n\nThat's what you see:" if user_text else "That's what you see:",
                image_content
            ]
            
            # Execute robot response
            llm_response, self.is_idle = await self.llm_agent.generate_say_execute_response(
                user_input, message_history, self.tts, self.sound_module, is_idle=self.is_idle
            )
            
            print()
            message_history.extend(llm_response)
            print(f"[TASK] Step done. Is idle: {self.is_idle}")
            
            # Continue or incorporate new commands
            if not self.is_idle:
                if self.sound_module.stt_output is not None:
                    user_text = self.sound_module.stt_output
                    self.sound_module.stt_output = None
                    print(f"[TASK] New command: '{user_text}'")
                else:
                    user_text = ""
                    
        print("[TASK] Completed")