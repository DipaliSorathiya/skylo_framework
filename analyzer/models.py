from dataclasses import dataclass

@dataclass
class Msg3Record:
    timestamp: str
    rnti: str
    message_type: str
    status: str