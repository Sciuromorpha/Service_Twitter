from sciuromorpha_core import static as S
from functools import cached_property, cache
from nameko.rpc import rpc, RpcProxy
from nameko.events import event_handler, BROADCAST, SERVICE_POOL
from nameko.standalone.rpc import ClusterRpcProxy
from sciuromorpha_service_twitter.config import config


class Twitter:
    name = "twitter"

    meta_rpc = RpcProxy("meta")
    storage_rpc = RpcProxy("storage")

    @classmethod
    @property
    @cache
    def storage_config(cls) -> dict:
        with ClusterRpcProxy(config) as cluster_rpc:
            storage_config = cluster_rpc.storage.get_service_path({"name": cls.name})

        return storage_config

    @classmethod
    @property
    def service_path(cls) -> str:
        return cls.storage_config["service_path"]

    @event_handler("meta", "create", handler_type=SERVICE_POOL)
    @event_handler("meta", "merge", handler_type=SERVICE_POOL)
    def handle_meta_event(self, meta_data: dict):
        origin_url = meta_data.get(S.META_KEY_ORIGIN_URL, None)

        if type(origin_url) is not str:
            # Silent failed.
            return

        # Process twitter URL info.

    @rpc
    def fetch(self, meta: dict) -> dict:
        pass

    @rpc
    def download_media(self, meta: dict) -> dict:
        pass
