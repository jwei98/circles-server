"""
All authentication convenience functions for connectig to Neo4j and FCM.
"""
from google.cloud import datastore


def neo4j_creds():
    """Gets the host, username, and password from Datastore."""
    # Get auth variables from cloud datastore.
    datastore_client = datastore.Client()
    query = datastore_client.query(kind='GaeEnvSettings')
    env_vars = list(query.fetch())[0]
    return env_vars['NEO4J_HOST'], env_vars['NEO4J_USERNAME'], env_vars['NEO4J_PASSWORD']


def fcm_creds():
    """Google Firestore Cloud Messaging auth."""
    datastore_client = datastore.Client()
    query = datastore_client.query(kind='GaeEnvSettings')
    env_vars = list(query.fetch())[0]
    return env_vars['FCM_API_KEY']
