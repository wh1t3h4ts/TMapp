"""Controller for secure credential CRUD operations."""
import logging
from datetime import datetime
from typing import List, Optional

from src.core.database import Database
from src.core.credential_crypto import encrypt_field, decrypt_field
from src.models.credential import Credential

logger = logging.getLogger(__name__)


class CredentialController:
    """
    Manages credential storage.

    The credential passphrase is kept in memory only while the vault is
    unlocked.  Calling lock() zeros it out.
    """

    def __init__(self, db: Database):
        self.db = db
        self._passphrase: Optional[str] = None   # in-memory only
        self._ensure_table()

    # ── Passphrase session ────────────────────────────────────────────────────
    def unlock(self, passphrase: str):
        """Cache passphrase for the current session."""
        self._passphrase = passphrase

    def lock(self):
        """Zero and discard the cached passphrase."""
        if self._passphrase:
            self._passphrase = "\x00" * len(self._passphrase)
        self._passphrase = None

    @property
    def is_unlocked(self) -> bool:
        return self._passphrase is not None

    # ── Schema ────────────────────────────────────────────────────────────────
    def _ensure_table(self):
        """Create credentials table if it doesn't exist (additive migration)."""
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id              TEXT PRIMARY KEY,
                note_id         TEXT,
                service         TEXT NOT NULL,
                category        TEXT DEFAULT 'web',
                username_enc    TEXT DEFAULT '',
                password_enc    TEXT DEFAULT '',
                url             TEXT DEFAULT '',
                totp_secret_enc TEXT,
                custom_fields_enc TEXT,
                created_at      TEXT NOT NULL,
                modified_at     TEXT NOT NULL
            )
        """)
        self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_cred_service
            ON credentials(service)
        """)

    # ── CRUD ──────────────────────────────────────────────────────────────────
    def create(self, service: str, username: str, password: str,
               url: str = "", category: str = "web",
               totp_secret: str = "", custom_fields: Optional[dict] = None,
               note_id: Optional[str] = None) -> Optional[Credential]:
        """Create and persist a new credential entry."""
        if not self.is_unlocked:
            raise RuntimeError("Credential vault is locked")
        try:
            import json
            cred = Credential.create_new(service, category, url, note_id)
            cred.username_enc = encrypt_field(username, self._passphrase)
            cred.password_enc = encrypt_field(password, self._passphrase)
            if totp_secret:
                cred.totp_secret_enc = encrypt_field(totp_secret, self._passphrase)
            if custom_fields:
                cred.custom_fields_enc = encrypt_field(
                    json.dumps(custom_fields), self._passphrase)

            d = cred.to_dict()
            self.db.execute("""
                INSERT INTO credentials
                    (id, note_id, service, category, username_enc, password_enc,
                     url, totp_secret_enc, custom_fields_enc, created_at, modified_at)
                VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """, (d["id"], d["note_id"], d["service"], d["category"],
                  d["username_enc"], d["password_enc"], d["url"],
                  d["totp_secret_enc"], d["custom_fields_enc"],
                  d["created_at"], d["modified_at"]))
            logger.info(f"Created credential: {cred.id} ({service})")
            return cred
        except Exception as e:
            logger.error(f"Failed to create credential: {e}")
            raise

    def update(self, cred_id: str, service: str, username: str, password: str,
               url: str = "", category: str = "web",
               totp_secret: str = "", custom_fields: Optional[dict] = None) -> bool:
        """Update an existing credential."""
        if not self.is_unlocked:
            raise RuntimeError("Credential vault is locked")
        try:
            import json
            now = datetime.now().isoformat()
            username_enc = encrypt_field(username, self._passphrase).hex()
            password_enc = encrypt_field(password, self._passphrase).hex()
            totp_enc = encrypt_field(totp_secret, self._passphrase).hex() if totp_secret else None
            cf_enc = encrypt_field(json.dumps(custom_fields), self._passphrase).hex() \
                     if custom_fields else None

            self.db.execute("""
                UPDATE credentials SET
                    service=?, category=?, username_enc=?, password_enc=?,
                    url=?, totp_secret_enc=?, custom_fields_enc=?, modified_at=?
                WHERE id=?
            """, (service, category, username_enc, password_enc,
                  url, totp_enc, cf_enc, now, cred_id))
            logger.info(f"Updated credential: {cred_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update credential {cred_id}: {e}")
            return False

    def delete(self, cred_id: str) -> bool:
        """Permanently delete a credential."""
        try:
            self.db.execute("DELETE FROM credentials WHERE id=?", (cred_id,))
            logger.info(f"Deleted credential: {cred_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete credential {cred_id}: {e}")
            return False

    def get_all(self) -> List[Credential]:
        """Return all credentials (encrypted blobs intact — not decrypted)."""
        rows = self.db.query_all(
            "SELECT * FROM credentials ORDER BY service ASC")
        return [Credential.from_dict(dict(r)) for r in rows]

    def get(self, cred_id: str) -> Optional[Credential]:
        """Return a single credential by ID."""
        row = self.db.query_one(
            "SELECT * FROM credentials WHERE id=?", (cred_id,))
        return Credential.from_dict(dict(row)) if row else None

    def decrypt_username(self, cred: Credential) -> str:
        if not self.is_unlocked:
            raise RuntimeError("Credential vault is locked")
        return decrypt_field(cred.username_enc, self._passphrase)

    def decrypt_password(self, cred: Credential) -> str:
        if not self.is_unlocked:
            raise RuntimeError("Credential vault is locked")
        return decrypt_field(cred.password_enc, self._passphrase)

    def decrypt_totp_secret(self, cred: Credential) -> str:
        if not self.is_unlocked or not cred.totp_secret_enc:
            return ""
        return decrypt_field(cred.totp_secret_enc, self._passphrase)

    def decrypt_custom_fields(self, cred: Credential) -> dict:
        if not self.is_unlocked or not cred.custom_fields_enc:
            return {}
        import json
        return json.loads(decrypt_field(cred.custom_fields_enc, self._passphrase))

    def search(self, query: str) -> List[Credential]:
        """Search by service, category, or url (all plaintext fields)."""
        q = f"%{query.lower()}%"
        rows = self.db.query_all("""
            SELECT * FROM credentials
            WHERE lower(service) LIKE ?
               OR lower(category) LIKE ?
               OR lower(url) LIKE ?
            ORDER BY service ASC
        """, (q, q, q))
        return [Credential.from_dict(dict(r)) for r in rows]

    def count(self) -> int:
        row = self.db.query_one("SELECT COUNT(*) as c FROM credentials")
        return row["c"] if row else 0
