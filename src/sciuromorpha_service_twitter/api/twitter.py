from sciuromorpha_core import static as S
from functools import cached_property, cache
import tweepy
from nameko.rpc import rpc, RpcProxy
from nameko.events import event_handler, BROADCAST, SERVICE_POOL
from nameko.standalone.rpc import ClusterRpcProxy
from sciuromorpha_service_twitter.config import amqp_config, twitter_config
from sciuromorpha_service_twitter.exceptions import SecretMissingError


class Twitter:
    name = "twitter"

    meta_rpc = RpcProxy("meta")
    secret_rpc = RpcProxy("secret")

    @classmethod
    def get_app_key(name: str = "default") -> str:
        return f"app_{name}_key"

    @classmethod
    def get_request_token_key(token: str) -> str:
        return f"request_{token}_token"

    @classmethod
    def get_access_key(key: str) -> str:
        return f"access_{key}_key"

    @classmethod
    def get_account_key(name: str = "default") -> str:
        return f"user_{name}_key"

    @classmethod
    @property
    @cache
    def storage_config(cls) -> dict:
        with ClusterRpcProxy(amqp_config) as cluster_rpc:
            storage_config = cluster_rpc.storage.get_service_path({"name": cls.name})

        return storage_config

    @classmethod
    @property
    def service_path(cls) -> str:
        return cls.storage_config["service_path"]

    @classmethod
    @property
    def storage_path(cls) -> str:
        return cls.storage_config["storage_path"]

    @event_handler("meta", "create", handler_type=SERVICE_POOL)
    @event_handler("meta", "merge", handler_type=SERVICE_POOL)
    def handle_meta_event(self, meta_data: dict):
        origin_url = meta_data.get(S.META_KEY_ORIGIN_URL, None)

        if type(origin_url) is not str:
            # Silent failed.
            return

        # Process twitter URL info.

    @rpc
    def setup_app(self, app_meta: dict) -> int:
        # Insert/Update app keys&secrets.
        name = app_meta.get("name", "default")
        api_key = app_meta.get("api_key", None)
        api_secret = app_meta.get("api_secret", None)
        bearer_token = app_meta.get("bearer_token", None)
        client_id = app_meta.get("client_id", None)
        client_secret = app_meta.get("client_secret", None)

        # TODO: Check the three key should at least had one inside.
        api_meta = {
            "name": self.name,
            "key": self.get_app_key(name),
            "data": {
                "api_key": api_key,
                "api_secret": api_secret,
                "bearer_token": bearer_token,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        }

        return self.secret_rpc.put(api_meta)

    @cache
    def get_app_meta(self, app_name: str = "default") -> dict:
        with ClusterRpcProxy(amqp_config) as cluster_rpc:
            app_meta = cluster_rpc.secret.get(
                {
                    "name": self.name,
                    "key": self.get_app_key(app_name),
                }
            )

        if (type(app_meta) is not dict) or (type(app_meta["data"]) is not dict):
            raise SecretMissingError(f"App {app_name} secret meta is missing.")

        return app_meta

    @rpc
    def get_oauth1_url(self, app_name: str = "default") -> str:
        api_meta = self.get_app_meta(app_name)
        api_secret = api_meta["data"]

        oauth1_user_handler = tweepy.OAuth1UserHandler(
            api_secret["api_key"],
            api_secret["api_secret"],
            callback=twitter_config["callback_url"],
        )

        result = oauth1_user_handler.get_authorization_url(signin_with_twitter=True)

        request_token = oauth1_user_handler.request_token["oauth_token"]
        request_secret = oauth1_user_handler.request_token["oauth_token_secret"]

        # Save request token for later callback usage.

        self.secret_rpc.put(
            {
                "name": self.name,
                "key": self.get_request_token_key(request_token),
                "data": {
                    "app_name": app_name,
                    "request_token": request_token,
                    "request_secret": request_secret,
                },
            }
        )

        return result

    @rpc
    def oauth1_get_access_token(self, oauth_token: str, oauth_verifier: str) -> str:
        request_meta = self.secret_rpc.get(
            {
                "name": self.name,
                "key": self.get_request_token_key(oauth_token),
            }
        )

        if type(request_meta) is not dict:
            raise SecretMissingError(
                f"Request token {oauth_token} secret meta is missing."
            )

        request_secret = request_meta["data"]
        app_name = request_secret.get("app_name", "default")

        api_meta = self.get_app_meta(app_name)
        api_secret = api_meta["data"]

        oauth1_user_handler = tweepy.OAuth1UserHandler(
            api_secret["api_key"],
            api_secret["api_secret"],
            callback=twitter_config["callback_url"],
        )

        oauth1_user_handler.request_token = {
            "oauth_token": request_secret["request_token"],
            "oauth_token_secret": request_secret["request_secret"],
        }

        access_token, access_secret = oauth1_user_handler.get_access_token(
            oauth_verifier
        )

        self.secret_rpc.put(
            {
                "name": self.name,
                "key": self.get_access_key(access_token),
                "data": {
                    "app_name": app_name,
                    "access_token": access_token,
                    "access_secret": access_secret,
                },
            }
        )

    @rpc
    def fetch(self, meta: dict) -> dict:
        pass

    @rpc
    def download_media(self, meta: dict) -> dict:
        pass
