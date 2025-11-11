import socket
import threading
from game_manager import GameManager
from protocol import Protocol

HOST= "localhost"
PORT= 5000

class GomokuServer:
    def __init__(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST,PORT))
        self.server_socket.listen()
        self.game_manager = GameManager()

    def handle_client(self, connect_socket, addr):
        print(f"Connected: {addr}")
        while True:
            try:
                data=connect_socket.recv(1024).decode()
                if not data:
                    break
                message = Protocol.parse(data)
                self.game_manager.process_message(connect_socket, message)
            except Exception as e:
                print(f"Error: {e}")
                break
        connect_socket.close()
        print(f"Disconnected: {addr}")
    
    def run(self):
        print(f"Server started on {HOST}:{PORT}")
        while True:
            connect, addr = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(connect, addr), daemon=True).start()

if __name__=="__main__":
    GomokuServer().run()

