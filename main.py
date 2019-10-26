"""
Main driver for Flask server.
"""
import os

from flask import Flask
from py2neo import Graph

import auth
from Models import Person

app = Flask(__name__)

# Connect to Neo4j graph.
host, username, password = auth.neo4j_creds()
graph = Graph(host=host, username=username, password=password, secure=True)


@app.route('/')
def hello():
    return 'Hello, Circles!!'


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
