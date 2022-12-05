from sciuromorpha_core import static as S
from nameko.rpc import rpc
from nameko.events import event_handler, BROADCAST, SERVICE_POOL


class Twitter:
    name = "twitter"

    @event_handler("meta", "create", handler_type=SERVICE_POOL)
    def handle_meta_event(self, meta_data: dict):
        origin_url = meta_data.get(S.META_KEY_ORIGIN_URL, None)
