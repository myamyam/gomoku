import socket
import threading
from protocol import Protocol
from board import Board
from chat import ChatHandler

HOST= "localhost"
PORT= 5000

class GomokuClient:
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.board = Board()

    def receive_messages(self):
        while True:
            data=self.client_socket.recv(1024).decode()
            if not data:
                break
            message = Protocol.parse(data)
            print(f"[SERVER] {message}")

    def run(self):
        self.client_socket.connect((HOST, PORT))
        threading.Thread(target=self.receive_messages, daemon=True).start()
        while True:
            text=input("> ")
            if text.lower()=='quit':
                break
            message=Protocol.encode("CHAT", {"text":text})
            self.client_socket.send(message.encode())

if __name__=="__main__":
    GomokuClient().run()

