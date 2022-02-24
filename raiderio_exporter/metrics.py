from prometheus_client import Gauge

CHARACTER_LABELS = ["name", "realm"]

ITEM_LEVEL = Gauge(
    "wow_character_item_level", "WoW Character's Item Level", CHARACTER_LABELS
)
RAID_PROGRESS = Gauge(
    "wow_character_raid_progress",
    "WoW Character's Raid Progress",
    ["raid", "difficulty", *CHARACTER_LABELS],
)
MYTHIC_PLUS_SCORE = Gauge(
    "wow_character_mplus_score",
    "WoW Character's Mythic+ Score",
    ["role", *CHARACTER_LABELS],
)
