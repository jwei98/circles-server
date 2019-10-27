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


@app.route('circles/api/v1.0/users/<int:user_id>', methods=['GET'])
def get_person(user_id):
    return """""{"person": {
        "username": "cooldude",
		"display_name": "Cool Dude", 
		"uid": "stuff",
		"email": "cooldude@duke.edu:,
		"photo": "base64",
		"Knows": [],
		"Circles": [],
		"InvitedTo": [],
    }
}"""


# @app.route('circles/api/v1.0/users/<int:user_id>', methods=['POST'])
# def add_person(user_id):
#     if not request.json:
#         abort(400)
#     # Use Circle model to add to graph
#
#     return
#
#
# @app.route('circles/api/v1.0/users/<int:user_id>', methods=['PUT'])
# def update_person(user_id):
#     if not request.json:
#         abort(400)
#     # Use Circle model to add to graph
#
#     return
#
# # Circle API
#
#
# @app.route('circles/api/v1.0/circles/<int:circle_id>', methods=['GET'])
# def get_circle(circle_id):
#     return
#
#
# @app.route('circles/api/v1.0/circles/<int:circle_id>', methods=['POST'])
# def create_circle(circle_id):
#     if not request.json:
#         abort(400)
#     # Use Circle model to add to graph
#
#     return
#
#
# @app.route('circles/api/v1.0/circles/<int:circle_id>', methods=['PUT'])
# def update_circle(circle_id):
#     if not request.json:
#         abort(400)
#     # Use Circle model to update in graph
#
#     return
# # Event API
#
#
# @app.route('circles/api/v1.0/events/<int:event_id>', methods=['GET'])
# def get_circle(event_id):
#     return
#
#
# @app.route('circles/api/v1.0/events/<int:event_id>', methods=['POST'])
# def create_event(event_id):
#     if not request.json:
#         abort(400)
#     # Use Event model to create and link to graph
#
#     return
#
#
# @app.route('circles/api/v1.0/events/<int:event_id>', methods=['PUT'])
# def update_event(event_id):
#     if not request.json:
#         abort(400)
#     # Use Event model to update in graph
#
#     return


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
