"""Credential data model for secure credential storage."""
import uuid
import json
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict


@dataclass
class Credential:
    """Secure credential entry — all sensitive fields stored encrypted."""

    id: str
    note_id: Optional[str]          # linked note (optional)
    service: str                     # plaintext — used for list display
    category: str                    # plaintext — e.g. "web", "ssh", "api"
    username_enc: bytes              # AES-256-GCM blob
    password_enc: bytes              # AES-256-GCM blob
    url: str                         # plaintext
    totp_secret_enc: Optional[bytes] # AES-256-GCM blob or None
    custom_fields_enc: Optional[bytes]  # JSON dict encrypted
    created_at: datetime
    modified_at: datetime

    @staticmethod
    def create_new(service: str, category: str = "web",
                   url: str = "", note_id: Optional[str] = None) -> "Credential":
        now = datetime.now()
        return Credential(
            id=str(uuid.uuid4()),
            note_id=note_id,
            service=service,
            category=category,
            username_enc=b"",
            password_enc=b"",
            url=url,
            totp_secret_enc=None,
            custom_fields_enc=None,
            created_at=now,
            modified_at=now,
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "note_id": self.note_id,
            "service": self.service,
            "category": self.category,
            "username_enc": self.username_enc.hex() if self.username_enc else "",
            "password_enc": self.password_enc.hex() if self.password_enc else "",
            "url": self.url,
            "totp_secret_enc": self.totp_secret_enc.hex() if self.totp_secret_enc else None,
            "custom_fields_enc": self.custom_fields_enc.hex() if self.custom_fields_enc else None,
            "created_at": self.created_at.isoformat(),
            "modified_at": self.modified_at.isoformat(),
        }

    @staticmethod
    def from_dict(data: dict) -> "Credential":
        def _hex(v):
            return bytes.fromhex(v) if v else b""

        def _hex_opt(v):
            return bytes.fromhex(v) if v else None

        return Credential(
            id=data["id"],
            note_id=data.get("note_id"),
            service=data["service"],
            category=data.get("category", "web"),
            username_enc=_hex(data.get("username_enc", "")),
            password_enc=_hex(data.get("password_enc", "")),
            url=data.get("url", ""),
            totp_secret_enc=_hex_opt(data.get("totp_secret_enc")),
            custom_fields_enc=_hex_opt(data.get("custom_fields_enc")),
            created_at=datetime.fromisoformat(data["created_at"]),
            modified_at=datetime.fromisoformat(data["modified_at"]),
        )
