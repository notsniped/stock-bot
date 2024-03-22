# Imports
import json
from framework.isobot.colors import Colors as colors
from discord import User

# Functions
class Weather():
    """Class to manage the weather db"""
    def __init__(self):
        print(f"[Framework/Loader] {colors.green}Weather database initialized.{colors.end}")

    def load(self) -> dict:
        """Fetches and returns the latest data from the levelling database."""
        with open("database/weather.json", 'r', encoding="utf-8") as f: db = json.load(f)
        return db

    def save(self, data: dict) -> int:
        """Dumps all cached data to your local machine."""
        with open("database/weather.json", 'w+', encoding="utf-8") as f: json.dump(data, f)
        return 0

    def new(self, user_id: User):
        user_db = self.load()
        if str(user_id) not in user_db: user_db[str(user_id)] = {"location": None, "scale": "Celsius"}
        self.save(user_db)
        return 0

    def set_scale(self, user_id: User, scale: str) -> int:
        user_db = self.load()
        user_db[str(user_id)]["scale"] = scale
        self.save(user_db)
        return 0

    def set_default_location(self, user_id: User, location: str) -> int:
        user_db = self.load()
        user_db[str(user_id)]["location"] = location
        self.save(user_db)
        return 0

    def get_scale(self, user_id: User):
        user_db = self.load()
        return user_db[str(user_id)]["scale"]

    def get_default_location(self, user_id: User):
        user_db = self.load()
        return user_db[str(user_id)]["location"]
