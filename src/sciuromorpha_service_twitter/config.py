from . import static as S
from sciuromorpha_core.config import config as core_config
from nameko.constants import AMQP_URI_CONFIG_KEY

config = {
    AMQP_URI_CONFIG_KEY: core_config[S.CONFIG_SECTION_MESSAGEQUEUE]["url"]
}