import asyncio
import websockets
import json

rooms = {}  # { room_id: {"players": [], "spectators": [], "board": [], "turn": 0} }

async def send(ws, msg_type, data):
    try:
        await ws.send(json.dumps({"type": msg_type, "data": data}))
    except:
        pass

async def broadcast_all(msg_type, data):
    for room in rooms.values():
        for ws in room["players"] + room["spectators"]:
            await send(ws, msg_type, data)

async def update_room_list():
    while True:
        await asyncio.sleep(1.5)
        room_data = []
        for room_id, info in rooms.items():
            room_data.append({
                "room_id": room_id,
                "players": len(info["players"]),
                "status": "waiting" if len(info["players"]) < 2 else "full"
            })
        await broadcast_all("ROOM_LIST", {"rooms": room_data})
        print("[ROOM_LIST]", room_data)  # ✅ 서버 확인 로그

async def handler(ws):
    current_room = None
    try:
        async for raw in ws:
            msg = json.loads(raw)
            t = msg["type"]
            data = msg["data"]

            # ✅ 새 방 생성
            if t == "CREATE_ROOM":
                room_id = f"room{len(rooms) + 1}"
                rooms[room_id] = {
                    "players": [ws],
                    "spectators": [],
                    "board": [["." for _ in range(15)] for _ in range(15)],
                    "turn": 0
                }
                await send(ws, "ROOM_CREATED", {"room_id": room_id})
                print(f"[+] Room {room_id} created")

            # ✅ 방 입장 (플레이어 or 관전자)
            elif t == "JOIN_ROOM":
                room_id = data["room_id"]
                if room_id in rooms:
                    room = rooms[room_id]
                    if len(room["players"]) < 2:
                        room["players"].append(ws)
                        await send(ws, "JOIN_SUCCESS", {"room_id": room_id, "role": "player"})
                        print(f"[+] Player joined {room_id}")
                    else:
                        room["spectators"].append(ws)
                        await send(ws, "JOIN_SUCCESS", {"room_id": room_id, "role": "spectator"})
                        print(f"[👁️] Spectator joined {room_id}")
                else:
                    await send(ws, "ERROR", {"msg": "해당 방이 존재하지 않습니다."})

            # ✅ 착수
            elif t == "MOVE":
                room_id = data["room_id"]
                x, y, stone = data["x"], data["y"], data["stone"]
                room = rooms.get(room_id)
                if room:
                    if 0 <= x < 15 and 0 <= y < 15 and room["board"][y][x] == ".":
                        room["board"][y][x] = stone
                        await broadcast_all("MOVE", {"x": x, "y": y, "stone": stone})
            # ✅ 채팅
            elif t == "CHAT":
                room_id = data["room_id"]
                msg_text = data["msg"]
                sender = data.get("sender", "익명")
                await broadcast_all("CHAT", {"room_id": room_id, "sender": sender, "msg": msg_text})
    except Exception as e:
        print("[Error]", e)

async def main():
    print("🚀 WebSocket 서버 실행 중 ws://localhost:5000")
    asyncio.create_task(update_room_list())  # ✅ 항상 방 상태 브로드캐스트
    async with websockets.serve(handler, "localhost", 5000):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())