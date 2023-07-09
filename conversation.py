from collections import deque


class Conversation:
    def __init__(self, max_length=10):
        self.messages = deque(maxlen=max_length)
        self.messages.append(
            {"role": "system", "content": f"You are answering questions about the knowledge you know."})

    def add_user_message(self, content):
        self.messages.append({"role": "user", "content": content})

    def add_model_message(self, content):
        self.messages.append({"role": "assistant", "content": content})
