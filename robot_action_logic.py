from pydantic_ai import BinaryContent
from camera import take_picture
from LLM_and_saying import LLMAndSaying




async def execute_robot_action_step(user_text, sound_module, llm_agent, tts, video_service, vid_handle, message_history, is_idle):
    """Execute a single step of robot's task - analyze environment, process command, perform actions"""
    # Capture and analyze environment
    camera_view_bytes = take_picture(video_service, vid_handle)
    image_content = BinaryContent(data=camera_view_bytes, media_type='image/jpeg')

    # Prepare input for robot's decision making
    user_input = [
        f"Human voice commend: '{user_text}'.\n\nThat's what you see on the front:" if user_text else "That's what you see on the front:",
        image_content
    ]

    # Execute robot's response (movement, speech, or other actions)
    llm_response, new_idle_state = await llm_agent.generate_say_execute_response(
        user_input,
        message_history,
        tts,
        sound_module,
        is_idle=is_idle
    )

    print()  # Add newline after streaming
    message_history.extend(llm_response)

    return new_idle_state


async def execute_robot_task(initial_command, sound_module, llm_agent, tts, video_service, vid_handle):
    """Execute the complete robot task from initial command until task completion"""
    print(f"[ROBOT_TASK] Starting robot task with initial command: '{initial_command}'")
    message_history = []
    is_idle = False
    user_text = initial_command

    # Execute task steps until completion
    print(f"[ROBOT_TASK] Entering task execution loop...")
    while not is_idle:
        print(f"[ROBOT_TASK] Executing action step with command: '{user_text}'")
        is_idle = await execute_robot_action_step(
            user_text, sound_module, llm_agent, tts,
            video_service, vid_handle, message_history, is_idle
        )
        print(f"[ROBOT_TASK] Action step completed. Is idle: {is_idle}")

        # If task not complete, continue with empty command (robot should continue working)
        # But check if new voice command arrived and incorporate it
        if not is_idle:
            if sound_module.stt_output is not None:
                user_text = sound_module.stt_output
                sound_module.stt_output = None
                print(f"[ROBOT_TASK] Got new command during task: '{user_text}' - incorporating into task")
            else:
                user_text = ""  # Continue with empty command - robot keeps working
                print(f"[ROBOT_TASK] No new command, continuing task execution...")

    print(f"[ROBOT_TASK] Task completed successfully, exiting loop")
