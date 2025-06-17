
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


def load_system_message():
    """Load system message from .prompt file"""
    with open('prompts/system_message.prompt', 'r', encoding='utf-8') as f:
        return f.read().strip()


def trim_history(messages, max_size=6):
    """Keep system message + last max_size conversation messages"""
    if len(messages) <= max_size:
        return messages

    # Zachowaj pierwszą wiadomość (zawiera system prompt) + ostatnie (max_size-1) wiadomości
    return [messages[0]] + messages[-(max_size - 1):]
