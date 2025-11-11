import threading
from protocol import Protocol

class ChatHandler:
    def __init__(self, connect, nickname, role="player"):
        self.conn = connect
        self.nickname = nickname
        self.role = role
        self.running = True

    def start_receiver(self):
        thread = threading.Thread(target=self.receive_messages, daemon=True)
        thread.start()

    def receive_messages(self):
        while self.running:
            try:
                data = self.conn.recv(2048).decode()
                if not data:
                    print("[Disconnected]")
                    self.running = False
                    break

                msg = Protocol.parse(data)
                msg_type = msg.get("type")
                content = msg.get("data", {})

                if msg_type == "CHAT":
                    sender = content.get("sender", "???")
                    text = content.get("msg", "")
                    role = content.get("role", "")
                    prefix = "[Spectator]" if role == "spectator" else "[Player]"
                    print(f"{prefix} {sender}: {text}")

                elif msg_type == "SYSTEM":
                    print(f"[SYSTEM] {content.get('msg', '')}")

                elif msg_type == "INFO":
                    print(f"[INFO] {content.get('msg', '')}")

                elif msg_type == "ERROR":
                    print(f"[ERROR] {content.get('msg', '')}")

            except Exception as e:
                print(f"[Error] {e}")
                break

    def send_message(self, text):
        if not text.strip():
            return
        msg = Protocol.encode("CHAT", {
            "sender": self.nickname,
            "msg": text,
            "role": self.role
        })
        try:
            self.conn.send(msg.encode())
        except Exception as e:
            print(f"[Error] {e}")
            self.running = False

    def run(self):
        self.start_receiver()
        print("💬 Start chatting (Quit: /quit)")
        while self.running:
            text = input("> ")
            if text.lower() == "/quit":
                self.running = False
                break
            self.send_message(text)
        print("Quit.")