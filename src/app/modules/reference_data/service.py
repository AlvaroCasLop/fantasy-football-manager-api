import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent / "data"


class ReferenceDataService:
    """Service to load, cache, and query static reference data (skills, races, inducements, star players)."""

    def __init__(self) -> None:
        self._skills_data: dict[str, Any] | None = None
        self._skills_by_id: dict[str, dict[str, Any]] | None = None
        self._skills_by_name: dict[str, dict[str, Any]] | None = None
        self._elite_skills_set: set[str] | None = None
        self._races_data: dict[str, Any] | None = None
        self._inducements_data: list[dict[str, Any]] | None = None
        self._stars_data: list[dict[str, Any]] | None = None

    def _load_skills(self) -> dict[str, Any]:
        if self._skills_data is None:
            skills_path = DATA_DIR / "skills.json"
            if skills_path.exists():
                with open(skills_path, "r", encoding="utf-8") as f:
                    self._skills_data = json.load(f)
            else:
                self._skills_data = {}

            self._skills_by_id = {}
            self._skills_by_name = {}
            self._elite_skills_set = set()

            # Cache elite skill IDs and names
            for s in self._skills_data.get("elite_skills", []):
                self._elite_skills_set.add(str(s).strip().lower())

            # Index glossary entries by ID and by display name
            for item in self._skills_data.get("glossary", []):
                skill_id = str(item.get("id", "")).strip().lower()
                skill_name = str(item.get("name", "")).strip().lower()

                if skill_id:
                    self._skills_by_id[skill_id] = item
                if skill_name:
                    self._skills_by_name[skill_name] = item

                if item.get("is_elite") is True:
                    if skill_id:
                        self._elite_skills_set.add(skill_id)
                    if skill_name:
                        self._elite_skills_set.add(skill_name)

        return self._skills_data

    def is_elite_skill(self, skill_id_or_name: str | None) -> bool:
        """Checks if a skill is considered Elite based on its id or name."""
        if not skill_id_or_name:
            return False
        self._load_skills()
        normalized = skill_id_or_name.strip().lower()
        return normalized in (self._elite_skills_set or set())

    def get_elite_skills(self) -> list[str]:
        """Returns the list of elite skill ids defined in skills.json."""
        data = self._load_skills()
        return list(data.get("elite_skills", []))

    def get_skill(self, skill_id_or_name: str) -> dict[str, Any] | None:
        """Finds details of a skill by its id or display name."""
        self._load_skills()
        normalized = skill_id_or_name.strip().lower()
        if self._skills_by_id and normalized in self._skills_by_id:
            return self._skills_by_id[normalized]
        if self._skills_by_name and normalized in self._skills_by_name:
            return self._skills_by_name[normalized]
        return None

    def get_all_skills(self) -> list[dict[str, Any]]:
        """Returns the list of all skills."""
        data = self._load_skills()
        return list(data.get("glossary", []))

    def get_skills_data(self) -> dict[str, Any]:
        """Returns full skills dictionary including categories and category_map."""
        return self._load_skills()

    def get_races(self) -> dict[str, Any]:
        """Returns dictionary of races and positionals."""
        if self._races_data is None:
            races_path = DATA_DIR / "races.json"
            if races_path.exists():
                with open(races_path, "r", encoding="utf-8") as f:
                    self._races_data = json.load(f)
            else:
                self._races_data = {}
        return self._races_data

    def get_race(self, race_name: str) -> dict[str, Any] | None:
        """Returns details of a specific race by name (case-insensitive)."""
        races = self.get_races()
        normalized = race_name.strip().lower()
        for key, race in races.items():
            if key.lower() == normalized or str(race.get("name", "")).lower() == normalized:
                return race
        return None

    def get_inducements(self) -> list[dict[str, Any]]:
        """Returns list of inducements."""
        if self._inducements_data is None:
            inducements_path = DATA_DIR / "inducements.json"
            if inducements_path.exists():
                with open(inducements_path, "r", encoding="utf-8") as f:
                    self._inducements_data = json.load(f)
            else:
                self._inducements_data = []
        return self._inducements_data

    def get_stars(self) -> list[dict[str, Any]]:
        """Returns list of star players."""
        if self._stars_data is None:
            stars_path = DATA_DIR / "stars.json"
            if stars_path.exists():
                with open(stars_path, "r", encoding="utf-8") as f:
                    self._stars_data = json.load(f)
            else:
                self._stars_data = []
        return self._stars_data

    def get_star(self, star_id: str) -> dict[str, Any] | None:
        """Returns details of a specific star player by id or name."""
        stars = self.get_stars()
        normalized = star_id.strip().lower()
        for star in stars:
            if str(star.get("id", "")).lower() == normalized or str(star.get("name", "")).lower() == normalized:
                return star
        return None

    def resolve_skills(self, skill_ids: list[str]) -> list[dict[str, Any]]:
        """Resolves a list of skill IDs (or names) to their complete skill metadata."""
        resolved: list[dict[str, Any]] = []
        for s in skill_ids:
            skill = self.get_skill(s)
            if skill:
                resolved.append(skill)
            else:
                resolved.append({"id": s, "name": s, "is_elite": False, "category": "Unknown"})
        return resolved


reference_data_service = ReferenceDataService()

