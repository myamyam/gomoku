import asyncio
import websockets
import json

rooms = {}        # { room_id: {...} }
connections = set()

async def send(ws, msg_type, data):
    try:
        await ws.send(json.dumps({"type": msg_type, "data": data}))
    except:
        pass

async def broadcast_all(msg_type, data):
    for ws in list(connections):
        try:
            await send(ws, msg_type, data)
        except:
            connections.discard(ws)

async def update_room_list():
    while True:
        await asyncio.sleep(1.5)
        room_data = []
        for room_id, info in rooms.items():
            room_data.append({
                "room_id": room_id,
                "players": len(info["players"]),
                "spectators": len(info["spectators"]),
                "status": "waiting" if len(info["players"]) < 2 else "playing"
            })
        await broadcast_all("ROOM_LIST", {"rooms": room_data})
        print("[ROOM_LIST broadcast]", room_data)

def check_win(board, stone):
    directions = [(1,0),(0,1),(1,1),(1,-1)]
    for y in range(15):
        for x in range(15):
            if board[y][x] != stone:
                continue
            for dx,dy in directions:
                count=1
                nx,ny=x+dx,y+dy
                while 0<=nx<15 and 0<=ny<15 and board[ny][nx]==stone:
                    count+=1
                    nx+=dx; ny+=dy

                nx,ny=x-dx,y-dy
                while 0<=nx<15 and 0<=ny<15 and board[ny][nx]==stone:
                    count+=1
                    nx-=dx; ny-=dy
                if count==5:
                    return True

    return False

async def handler(ws):
    print("🟢 새 연결")
    connections.add(ws)

    try:
        async for raw in ws:
            msg = json.loads(raw)
            t = msg["type"]
            data = msg.get("data", {})

            # ✅ 방 생성 시 첫 번째 플레이어로 자동 등록
            if t == "CREATE_ROOM":
                nickname=data.get("nickname", "Player1")
                room_id = f"room{len(rooms) + 1}"
                rooms[room_id] = {
                    "players": [ws],
                    "spectators": [],
                    "board": [["." for _ in range(15)] for _ in range(15)]
                }
                await send(ws, "ROOM_CREATED", {"room_id": room_id})
                print(f"[+] Room {room_id} created — Player1 joined automatically")
                continue

            # ✅ 방 입장
            elif t == "JOIN_ROOM":
                room_id = data["room_id"]
                nickname = data.get("nickname", "Guest")
                role = data.get("role", "player")

                if room_id not in rooms:
                    await send(ws, "ERROR", {"msg": "존재하지 않는 방입니다."})
                    continue

                room = rooms[room_id]
                room["players"] = [p for p in room["players"] if p in connections]

                if len(room["players"]) < 2 and role =="player":
                    room["players"].append(ws)
                    stone="black" if len(room["players"])==1 else "white"
                    await send(ws, "JOIN_SUCCESS", {
                        "room_id": room_id, 
                        "role": "player", 
                        "nickname": nickname,
                        "stone":stone
                    })
                    print(f"[+] {nickname} joined {room_id} as player ({len(room['players'])}/2)")
                    if len(room["players"]) ==2:
                        await broadcast_all("TURN", {"next": "black"})
                else:
                    room["spectators"].append(ws)
                    await send(ws, "JOIN_SUCCESS", {
                        "room_id":room_id,
                        "role": "spectator",
                        "nickname":nickname
                    })
                    await send(ws, "BOARD_STATE", {"board":room["board"]})
                    print(f"[👁️] {nickname} joined {room_id} as spectator")
                room_data = []
                for rid, info in rooms.items():
                    room_data.append({
                        "room_id": rid,
                        "players": len(info["players"]),
                        "spectators": len(info["spectators"]),
                        "status": "waiting" if len(info["players"]) < 2 else "playing"
                    })
                await broadcast_all("ROOM_LIST", {"rooms": room_data})
            elif t == "MOVE":
                room_id = data["room_id"]
                x, y = data["x"], data["y"]
                
                if not room:
                    continue
                
                room=rooms[room_id]
                turn=room.get("turn",0)
                stone = "black" if turn == 0 else "white"
                board = room["board"]

                if not (0 <= x < 15 and 0 <= y < 15):
                    await send(ws, "INFO", {"msg": "좌표가 잘못되었습니다."})
                    continue

                if board[y][x] != ".":
                    await send(ws, "INFO", {"msg": "이미 돌이 있는 자리입니다."})
                    continue

                board[y][x] = stone
                room["turn"] = 1 - turn  # 턴 교대

                # 전체에 브로드캐스트
                await broadcast_all("MOVE", {"x": x, "y": y, "stone": stone})
                if check_win(board, stone):
                    print(f"[🏆] {stone} wins at move ({x}, {y})")
                    await broadcast_all("GAME_OVER", {"winner":stone})
                    room["board"]=[["." for _ in range(15)] for _ in range(15)]
                else:
                    await broadcast_all("TURN", {"next": "white" if room["turn"]==1 else "black"})    
            
            elif t=="CHAT":
                room_id=data["room_id"]
                text=data["msg"]
                sender=data.get("sender", "익명")
                await broadcast_all("CHAT", {"room_id": room_id, "msg":text, "sender":sender})

    except Exception as e:
        print("[Error]", e)

    finally:
        connections.discard(ws)
        for room in rooms.values():
            if ws in room["players"]:
                room["players"].remove(ws)
            if ws in room["spectators"]:
                room["spectators"].remove(ws)
        print("🔴 연결 해제")

async def main():
    print("🚀 WebSocket 서버 실행 중 ws://localhost:5000")
    asyncio.create_task(update_room_list())
    async with websockets.serve(handler, "localhost", 5000):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())