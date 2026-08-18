"""
Logger wrapper & load logger & validation
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


@dataclass(frozen=True)
class AppConfig:
    """Immutable application config wrapper"""

    raw: Dict[str, Any]
    
    @property
    def app_name(self) -> str:
        return str(self.raw.get("app", {}).get("name", "S.Y.N.C."))
    
    @property
    def version(self) -> str:
        return str(self.raw.get("app", {}).get("version", "0.1.0-alpha"))

    @property
    def codename(self) -> str:
        return str(self.raw.get("app", {}).get("codename", "Resonance"))
    
    @property
    def log_level(self) -> str:
        return str(self.raw.get("logging", {}).get("level", "INFO"))


def load_config(path: str | Path) -> AppConfig:
    """load and validate yaml file"""
    config_path = Path(path)

    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with config_path.open("r", encoding="utf-8") as file:
        parsed = yaml.safe_load(file) or {}
    
    if not isinstance(parsed, Dict):
        raise ValueError("Config root filt must be a dictionary/mapping")

    return AppConfig(raw=parsed)
