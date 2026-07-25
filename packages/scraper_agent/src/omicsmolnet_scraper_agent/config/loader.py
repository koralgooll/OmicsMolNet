from pathlib import Path

import yaml
from pydantic import BaseModel, field_validator


class ScraperConfig(BaseModel):
    ids: list[str]

    @field_validator("ids")
    @classmethod
    def ids_not_empty(cls, v: list[str]) -> list[str]:
        if not v:
            raise ValueError("ids list must contain at least one entry")
        return [entry.strip() for entry in v if entry.strip()]


def load_config(path: str | Path) -> ScraperConfig:
    """Load and validate the YAML config file containing protein IDs."""
    with open(path) as fh:
        data = yaml.safe_load(fh)
    return ScraperConfig.model_validate(data)
