class Player:
    def __init__(self, connect, nickname, symbol):
        """
        
        """
        self.connect=connect
        self.nickname=nickname
        self.symbol=symbol
        self.connected=True
        self.ready=False
        self.last_move_time=None
        self.is_spectator=False

    def send(self, msg):
        try:
            self.connect.send(msg.encode())
        except Exception:
            self.connected=False
    
    def mark_ready(self):
        self.ready=True
    
    def disconnect(self):
        self.connected=False
    
    def __repr__(self):
        role="Spectator" if self.is_spectator else "Player"
        return f"<{role} {self.nickname} ({'connected' if self.connected else 'disconnected'})>"