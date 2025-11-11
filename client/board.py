class Board:
    def __init__(self, size=15):
        self.size = size
        self.grid = [['.' for _ in range(size)] for _ in range(size)]
    
    def place_stone(self, x, y, stone):
        if self.grid[y][x] == '.':
            self.grid[y][x] = stone
            return True
        return False
    
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
                
# def check_win(self, row, col):
#     for d in self.directions:
#         count = 1
#         for i in range(1, 6):
#             r, c = row + d[0] * i, col + d[1] * i
#             if 0 <= r < 19 and 0 <= c < 19 and self.board[r][c] == self.current_player:
#                 count += 1
#             else:
#                 break

#         for i in range(1, 6):
#             r, c = row - d[0] * i, col - d[1] * i
#             if 0 <= r < 19 and 0 <= c < 19 and self.board[r][c] == self.current_player:
#                 count += 1
#             else:
#                 break

#         if count == 5:
#             return True
#     return False            