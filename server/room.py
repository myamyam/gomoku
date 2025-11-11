from protocol import Protocol
import threading
import time

BOARD_SIZE=15
TURN_TIME_LIMIT=30

class Room:
    def __init__(self, room_id):
        self.room_id=room_id
        self.players=[]
        self.spectators=[]
        self.board=[['.' for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.current_turn=0
        self.game_over=False

    def add_player(self, connect, nickname):
        if len(self.players)<2:
            self.players.append((connect, nickname))
            print(f"[Room {self.room_id}] Player joined: {nickname}")
            return True
        else:
            self.spectators.append(connect)
            connect.send(Protocol.encode("INFO", {"msg": "You are joined as spectator"}).encode())
            print(f"[Room {self.room_id}] Spectator connected")
            return False
    
    def remove_player(self, connect):
        self.players=[(c,n) for c,n in self.players if c!=connect]
        self.spectators=[c for c in self.spectators if c!=connect]
        print(f"[Room {self.room_id}] A connection left the room")
    
    def has_connection(self, connect):
        return any(connect==c for c,_ in self.players) or connect in self.spectators
    
    def is_full(self):
        return len(self.players)==2
    
    def is_empty(self):
        return len(self.players)==0 and len(self.spectators)==0
    
    def broadcast(self,msg):
        for connect,_ in self.players:
            try:
                connect.send(msg.encode())
            except:
                pass
        for connect in self.spectators:
            try:
                connect.send(msg.encode())
            except:
                pass
    
    def get_player_index(self, connect):
        for i, (c,_) in enumerate(self.players):
            if c==connect:
                return i
        return None
    
    def place_stone(self, connect, x, y):
        if self.game_over:
            connect.send(Protocol.encode("INFO", {"msg":"Game is ended"}).encode())
            return
        player_idx=self.get_player_index(connect)
        if player_idx is None:
            connect.send(Protocol.encode("ERROR", {"msg":"Spectators can't move"}).encode())
        if player_idx !=self.current_turn:
            connect.send(Protocol.encode("INFO", {"msg": "Not your turn"}).encode())
        if self.board[y][x]!='.':
            connect.send(Protocol.encode("INFO", {"msg": "Already occupied"}).encode())
            return
        
        stone='X' if player_idx==0 else 'O'
        self.board[y][x]=stone
        print(f"[Room {self.room_id}] Player {stone} placed ({x},{y})")

        self.broadcast(Protocol.encode("MOVE", {"x":x, "y":y, "stone": stone}))

        if self.check_win(x,y,stone):
            self.broadcast(Protocol.encode("GAME_OVER", {"winner": stone}))
            self.game_over=True
            print(f"[Room {self.room_id}] Winner: {stone}")
            return
        self.current_turn=1-self.current_turn
        next_player=self.players[self.current_turn][1]
        self.broadcast(Protocol.encode("TURN", {"next": next_player}))

    def check_win(self, x, y, stone):
        directions = [(1,0),(0,1),(1,1),(1,-1)]
        for dx, dy in directions:
            count=1
            for sign in [1, -1]:
                nx, ny = x, y
                while True:
                    nx+=dx*sign
                    ny+=dy*sign
                    if 0<=nx<self.size and 0<=ny<self.size and self.grid[ny][nx]==stone:
                        count+=1
                    else:
                        break
            if count == 5:
                return True
        return False
    
    def start_turn_timer(self):
        if hasattr(self, "timer_thread") and self.timer_thread.is_alive():
            self.timer_stop=True
            self.timer_thread.join()

        self.timer_stop=False
        self.timer_thread=threading.Thread(target=self.turn_timer)
        self.timer_thread.daemon=True
        self.timer_thread.start()

    def turn_timer(self):
        remaining=TURN_TIME_LIMIT
        while remaining>0 and not self.timer_stop:
            time.sleep(1)
            remaining-=1
        if not self.timer_stop:
            loser=self.players[self.current_turn][1]
            self.broadcast(Protocol.encode("TIMEOUT", {"loser": loser}))
            self.game_over=True