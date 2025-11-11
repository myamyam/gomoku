import json

class Protocol:
    @staticmethod
    def encode(msg_type, data):
        return json.dumps({"type": msg_type, "data": data})
    
    @staticmethod
    def parse(json_str):
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return {"type": "ERROR", "data": {"msg": "Invalid JSON"}}
        