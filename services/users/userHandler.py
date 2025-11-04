# Recibe datos del message
class UserHandler:
    def getSenderData(self, sender_info) -> dict:
        sender_data = {
            "name" : sender_info.get("profile", {})["name"].split(" ")[0] or None,
            "wa_id": sender_info.get("wa_id") or None
        }
        return sender_data
    

    def getSenderName(self, sender_info) -> bool:
        return sender_info.get("profile", {})["name"].split(" ")[0] or sender_info.get("wa_id") or ""