import logging

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from worker.core.config import Settings
from worker.es.index_definitions import INDEX_DEFINITIONS

logger = logging.getLogger(__name__)


class ElasticsearchWriter:
    def __init__(self, settings: Settings) -> None:
        basic_auth = None
        if settings.es_username:
            basic_auth = (settings.es_username, settings.es_password)

        self.client = Elasticsearch(
            settings.es_host,
            basic_auth=basic_auth,
            verify_certs=settings.es_verify_certs,
            request_timeout=60,
        )

    def health(self) -> dict:
        info = self.client.info()
        cluster_health = self.client.cluster.health()
        return {
            "cluster_name": info.get("cluster_name"),
            "version": info.get("version", {}).get("number"),
            "status": cluster_health.get("status"),
            "number_of_nodes": cluster_health.get("number_of_nodes"),
        }

    def initialize_indices(self) -> list[dict]:
        results: list[dict] = []
        for index_name, body in INDEX_DEFINITIONS.items():
            if self.client.indices.exists(index=index_name):
                logger.info("index already exists: %s", index_name)
                results.append({"index": index_name, "created": False})
                continue

            self.client.indices.create(index=index_name, **body)
            logger.info("created index: %s", index_name)
            results.append({"index": index_name, "created": True})

        return results

    def bulk_upsert(self, index_name: str, documents: list[dict]) -> dict:
        if not documents:
            return {"index": index_name, "upserted": 0}

        actions = []
        for document in documents:
            document_id = document["_id"]
            payload = {key: value for key, value in document.items() if key != "_id"}
            actions.append(
                {
                    "_op_type": "update",
                    "_index": index_name,
                    "_id": document_id,
                    "doc": payload,
                    "doc_as_upsert": True,
                }
            )

        success_count, _ = bulk(self.client, actions, stats_only=True, refresh="wait_for")
        return {"index": index_name, "upserted": success_count}
