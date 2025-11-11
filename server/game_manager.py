from room import Room
from protocol import Protocol

class GameManager:
    def __init__(self):
        self.rooms={}
        self.next_room_id=1

    def create_room(self, connect, nickname):
        room_id=str(self.next_room_id)
        self.next_room_id+=1
        new_room=Room(room_id)
        new_room.add_player(connect,nickname)
        self.rooms[room_id]=new_room
        connect.send(Protocol.encode("ROOM_CREATED", {"room_id": room_id}).encode())
        print(f"[+] Room {room_id} created by {nickname}")

    def join_room(self, connect, room_id, nickname):
        if room_id not in self.rooms:
            connect.send(Protocol.encode("ERROR", {"msg": "Room not found"}).encode())
            return
        room = self.rooms[room_id]
        result = room.add_player(connect, nickname)
        if result:
            connect.send(Protocol.encode("JOIN_SUCCESS", {"room_id": room_id}).encode())
            room.broadcast(Protocol.encode("SYSTEM", {"msg": f"{nickname} joined room."}))
        else:
            connect.send(Protocol.encode("ERROR", {"msg": "Room full"}).encode())
    
    def leave_room(self, connect):
        for room_id, room in list(self.rooms.items()):
            if room.has_connection(connect):
                room.remove_player(connect)
                room.broadcast(Protocol.encode("SYSTEM", {"msg": "A player has left the room"}))
                if room.is_empty():
                    del self.rooms[room_id]
                    print(f"[-] Room {room_id} removed")
                break

    def process_message(self, connect, message):
        msg_type = message["type"]
        data = message["data"]

        if msg_type == "CREATE_ROOM":
            self.create_room(connect, data["nickname"])
        elif msg_type == "JOIN_ROOM":
            self.join_room(connect, data["room_id"], data["nickname"])
        elif msg_type == "LEAVE_ROOM":
            self.leave_room(connect)
        elif msg_type == "MOVE":
            self.handle_move(connect, data)
        elif msg_type == "CHAT":
            self.handle_chat(connect, data)
        else:
            connect.send(Protocol.encode("ERROR", {"msg": f"Unknown message type: {msg_type}"}).encode())

    def handle_move(self, connect, data):
        for room in self.rooms.values():
            if room.has_connection(connect):
                x, y = data["x"], data["y"]
                room.place_stone(connect, x, y)
                break

    def handle_chat(self, connect, data):
        for room in self.rooms.values():
            if room.has_connection(connect):
                msg = data["text"]
                room.broadcast(Protocol.encode("CHAT", {"msg": msg}))
                break