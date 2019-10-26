"""
All authenticatio convenience functions.
"""
from google.cloud import datastore

# TODO: This should depend on environment we're in?
def graph_creds():
    # Get auth variables from cloud datastore.
    datastore_client = datastore.Client()
    query = datastore_client.query(kind='GaeEnvSettings')
    env_vars = list(query.fetch())[0]
    return env_vars['NEO4J_HOST'], env_vars['NEO4J_USERNAME'], env_vars['NEO4J_PASSWORD']
