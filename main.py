"""
Main driver for Flask server.
"""
import os

from flask import Flask, request, abort
from py2neo import Graph

import auth

app = Flask(__name__)

# Connect to Neo4j graph.
host, username, password = auth.neo4j_creds()
graph = Graph(host=host, username=username, password=password, secure=True)


@app.route('/')
def hello():
    return 'Hello, Circles!!'

# User API


@app.route('/circles/api/v1.0/users/<int:id>', methods=['GET'])
def get_person(id):
    return """
{
    "Person": {
        "id": %d,
        "display_name": "Cool Dude", 
        "email": "cooldude@duke.edu:,
        "photo": "base64",
        "Knows": [],
        "IsMember": [],
        "InvitedTo": []
    }
}""" % id


@app.route('/circles/api/v1.0/circles/<int:id>', methods=['GET'])
def get_circle(id):
    return """
{
    “Circle”: {
        “id”: %d,
        “display_name”: "Circle Display Name",
        “description”: "Awesome Description",
        “HasMember”: [1, 2, 3],
        “Scheduled”: [4, 5, 6]
    }
} """ % id


@app.route('/circles/api/v1.0/events/<int:id>', methods=['GET'])
def get_event(id):
    return """
{
    “Event”: {
    “id”: %d,
    “display_name”: "Event Display Name">,
    “description”: "Cool Event Description",
    “location”: "Location String",
    “datetime”: "Datetime Object",
    “BelongsTo”: 000,
    “Invited”: { [
        {1: true},
        {2: true},
        {3: false},
        ]
    }
}
"""

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
