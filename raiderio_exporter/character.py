import itertools
import logging
from datetime import datetime, timedelta

import requests

from raiderio_exporter.metrics import ITEM_LEVEL, MYTHIC_PLUS_SCORE, RAID_PROGRESS

CACHE_TIME = timedelta(hours=1)
RAID_DIFFICULTIES = ["normal", "heroic", "mythic"]


class CharacterNotFoundError(Exception):
    pass


class Character:
    def __init__(self, name, realm, region):
        self.name = name
        self.realm = realm
        self.region = region

        self._last_refreshed = None
        self._rio_profile = None

        self._raids = []
        self._mplus_roles = ["all"]

        self._log = logging.getLogger(__name__ + f":{region}/{realm}/{name}")

    @classmethod
    def from_config(cls, global_config, config):
        character = cls(config["name"], config["realm"], config["region"])

        # Default to global settings, allow per-character override
        raids = config.get("raids", global_config["raids"])
        if isinstance(raids, bool) and raids == False:
            character._raids = []
        elif isinstance(raids, list):
            character._raids = raids

        character._mplus_roles.extend(
            config.get("mplus_roles", global_config["mplus_roles"])
        )

        return character

    @property
    def labels(self):
        return {
            "name": self.name,
            "realm": f"{self.realm}-{self.region}",
        }

    def get_rio_profile(self):
        now = datetime.utcnow()
        if not self._last_refreshed or ((now - self._last_refreshed) > CACHE_TIME):
            self._log.info("Refreshing Character")
            resp = requests.get(
                f"https://raider.io/api/v1/characters/profile",
                params={
                    "region": self.region,
                    "realm": self.realm,
                    "name": self.name,
                    "fields": ",".join(
                        [
                            "gear",
                            "raid_progression",
                            "mythic_plus_scores_by_season:current",
                        ]
                    ),
                },
            )
            if resp.status_code != 200:
                raise CharacterNotFoundError()

            self._last_refreshed = now
            self._rio_profile = resp.json()

        return self._rio_profile

    def setup_collectors(self):
        ITEM_LEVEL.labels(**self.labels).set_function(self._collect_ilvl)

        for difficulty, raid in itertools.product(RAID_DIFFICULTIES, self._raids):
            self._log.debug(
                "Configuring Raid: %s %s",
                difficulty,
                raid,
            )
            RAID_PROGRESS.labels(
                raid=raid, difficulty=difficulty, **self.labels
            ).set_function(self._collect_raid_progress(raid, difficulty))

        for role in self._mplus_roles:
            self._log.debug("Configuring MPlus Role: %s", role)
            MYTHIC_PLUS_SCORE.labels(role=role, **self.labels).set_function(
                self._collect_mplus_score(role)
            )

    def _collect_ilvl(self):
        profile = self.get_rio_profile()
        return profile["gear"]["item_level_equipped"]

    def _collect_raid_progress(self, raid, difficulty):
        def collect():
            profile = self.get_rio_profile()
            return profile["raid_progression"][raid][f"{difficulty}_bosses_killed"]

        return collect

    def _collect_mplus_score(self, role):
        def collect():
            profile = self.get_rio_profile()
            season = profile["mythic_plus_scores_by_season"][0]
            return season["scores"][role]

        return collect
