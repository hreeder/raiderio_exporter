import logging
import os

import yaml
from prometheus_client import make_wsgi_app
from wsgiref.simple_server import make_server

from raiderio_exporter.character import Character, CharacterNotFoundError

logging.basicConfig(
    level=logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO").upper())
)
logger = logging.getLogger("raiderio_exporter.main")

app = make_wsgi_app()

with open(os.environ.get("CONFIG_PATH", "/etc/raiderio_exporter.yml")) as config_file:
    config = yaml.load(config_file, Loader=yaml.SafeLoader)

characters = [
    Character.from_config(config["global"], character)
    for character in config["characters"]
]

for character in characters:
    try:
        character.get_rio_profile()
    except CharacterNotFoundError:
        # If the Character can't be pulled, don't set up metrics for it
        # This means that we don't break the metrics deployment when a given
        # character does not exist
        logger.warning(
            "UNABLE TO FETCH CHARACTER [%s/%s/%s]",
            character.region,
            character.realm,
            character.name,
        )
        continue

    character.setup_collectors()


if __name__ == "__main__":
    httpd = make_server("127.0.0.1", 5123, app)
    httpd.serve_forever()
