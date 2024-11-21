import asyncio
from opensearchpy import AsyncOpenSearch
from opensearchpy.helpers import async_bulk
from opensearchpy.exceptions import NotFoundError

OPENSEARCH_HOST = 'https://127.0.0.1:9200'
OPENSEARCH_USER = 'admin'
OPENSEARCH_PASSWORD = ''
INDEX_NAME = 'logstash-2024.09.01'
NEW_INDEX_NAME = 'top_processes_by_cpu'

client = AsyncOpenSearch(
    hosts=[OPENSEARCH_HOST],
    http_auth=(OPENSEARCH_USER, OPENSEARCH_PASSWORD),
    scheme='https',
    port=9200,
    verify_certs=False
)

async def get_top_processes(client):
    try:
        response = await client.search(
            index=INDEX_NAME,
            body={
                "size": 0,
                "aggs": {
                    "top_processes": {
                        "terms": {
                            "field": "comm.keyword",
                            "size": 3,
                            "order": {"max_cpu": "desc"}
                        },
                        "aggs": {
                            "max_cpu": {
                                "max": {
                                    "field": "cpu"
                                }
                            }
                        }
                    }
                }
            }
        )
        buckets = response['aggregations']['top_processes']['buckets']
        if not buckets:
            print("No top processes found.")
            return []
        top_processes = [
            {
                '_op_type': 'update',
                '_index': NEW_INDEX_NAME,
                '_id': bucket['key'],
                'doc': {
                    'process_name': bucket['key'],
                    'max_cpu_usage': bucket['max_cpu']['value']
                },
                'doc_as_upsert': True
            }
            for bucket in buckets
        ]
        return top_processes

    except NotFoundError as e:
        print(f"Index not found: {e}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []

async def index_top_processes(client, top_processes):
    if not top_processes:
        return

    try:
        await async_bulk(client, top_processes)
        print("Top processes indexed successfully.")
    except Exception as e:
        print(f"Error indexing data: {e}")

async def main():
    try:
        top_processes = await get_top_processes(client)
        if top_processes:
            print("Top 3 CPU processes:")
            for process in top_processes:
                print(f"Process Name: {process['doc']['process_name']}, Max CPU Usage: {process['doc']['max_cpu_usage']}")
        else:
            print("No top processes found.")
        await index_top_processes(client, top_processes)
    finally:
        await client.close()

asyncio.run(main())