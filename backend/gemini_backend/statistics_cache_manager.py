import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any

from . import config


class StatisticsCacheManager:
    def __init__(self):
        self.cache_file = config.STATISTICS_CACHE_FILE
        self.cache_data = self._load_cache()

    def _load_cache(self) -> Dict[str, Any]:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_cache(self) -> None:
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w", encoding="utf-8") as f:
            json.dump(self.cache_data, f, indent=2)

    def calculate_component_hash(
        self,
        *,
        analysis_content: str,
        video_url: str,
        project_name: str,
        component_name: str,
        schema_version: int,
        prompt_version: str,
    ) -> str:
        payload = "|".join(
            [
                analysis_content,
                video_url,
                project_name,
                component_name,
                str(schema_version),
                prompt_version,
            ]
        )
        return hashlib.sha256(payload.encode("utf-8", errors="ignore")).hexdigest()

    def get_cached_component(self, cache_key: str) -> Optional[Dict[str, Any]]:
        entry = self.cache_data.get(cache_key)
        if not entry:
            return None

        expires_at_raw = entry.get("expires_at")
        if expires_at_raw:
            try:
                expires_at = datetime.fromisoformat(expires_at_raw)
                if datetime.utcnow() > expires_at:
                    del self.cache_data[cache_key]
                    self._save_cache()
                    return None
            except Exception:
                del self.cache_data[cache_key]
                self._save_cache()
                return None

        output_path_raw = entry.get("output_path")
        if not isinstance(output_path_raw, str) or not output_path_raw:
            return None

        output_path = Path(output_path_raw)
        if not output_path.exists():
            del self.cache_data[cache_key]
            self._save_cache()
            return None

        return entry

    def save_cached_component(
        self,
        cache_key: str,
        *,
        component_name: str,
        output_path: Path,
        schema_version: int,
        prompt_version: str,
        ttl_hours: int | None = None,
    ) -> None:
        now = datetime.utcnow()
        expires_at = None
        if ttl_hours is None:
            ttl_hours = getattr(config, "STATISTICS_CACHE_EXPIRY_HOURS", None)
        if isinstance(ttl_hours, int) and ttl_hours > 0:
            expires_at = now + timedelta(hours=ttl_hours)

        self.cache_data[cache_key] = {
            "component": component_name,
            "output_path": str(output_path),
            "schema_version": schema_version,
            "prompt_version": prompt_version,
            "saved_at": now.isoformat(),
            "expires_at": expires_at.isoformat() if expires_at else None,
        }
        self._save_cache()

    def cleanup_expired_cache(self) -> int:
        now = datetime.utcnow()
        expired_keys: list[str] = []

        for key, entry in self.cache_data.items():
            expires_at_raw = entry.get("expires_at")
            if not expires_at_raw:
                continue
            try:
                expires_at = datetime.fromisoformat(expires_at_raw)
                if now > expires_at:
                    expired_keys.append(key)
            except Exception:
                expired_keys.append(key)

        for key in expired_keys:
            self.cache_data.pop(key, None)

        if expired_keys:
            self._save_cache()

        return len(expired_keys)


statistics_cache_manager = StatisticsCacheManager()
