"""
Main driver for Flask server.
"""
import os
import json

from flask import Flask, request, jsonify
from py2neo import Graph, NodeMatcher

import auth
from Models import Person, Circle, Event

app = Flask(__name__)

# Connect to Neo4j graph.
host, username, password = auth.neo4j_creds()
graph = Graph(host=host, username=username, password=password, secure=True)


@app.route('/')
def hello():
    r = Person('Rishi', 'Temp@duke.edu', 'hello')
    graph.push(r)
    return 'Hello, Circles!!'


@app.route('/circles/api/v1.0/users/dummy/<int:person_id>', methods=['GET'])
def get_person_dummy(person_id):
    # Fetching details about a dummy user
    person_info = {
        'Person': {
            'id': person_id,
            'display_name': 'Cool Dude',
            'email': 'cooldude@duke.edu',
            'photo': 'base64',
            'Knows': [],
            'IsMember': [],
            'InvitedTo': []
        }
    }
    return json.dumps(person_info)

@app.route('/circles/api/v1.0/users/<int:person_id>', methods=['GET', 'POST'])
def get_person(person_id):
    # Fetching details about a user
    if request.method == 'GET':
        m = NodeMatcher(graph)
        match = m.get(person_id)
        return json.dumps(match)
    # Creating a new person
    if request.method == 'POST':
        name = request.json['display_name']
        email = request.json['email']
        photo = request.json['photo']
        p = Person(name, email, photo)
        graph.push(p)
        return jsonify(p)



@app.route('/circles/api/v1.0/circles/<int:circle_id>', methods=['GET'])
def get_circle(circle_id):
    circle_info = {
        'Circle': {
            'id': circle_id,
            'display_name': 'Circle Display Name',
            'description': 'Awesome Description',
            'HasMember': [1, 2, 3],
            'Scheduled': [4, 5, 6]
        }
    }
    return json.dumps(circle_info)


@app.route('/circles/api/v1.0/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    event_info = {
        'Event': {
            'id': event_id,
            'display_name': 'Event Display Name',
            'description': 'Cool Event Description',
            'location': 'Location String',
            'datetime': 'Datetime Object',
            'BelongsTo': 000,
            'Invited': {
                1: True,
                2: True,
                3: False,
            }
        }
    }
    return json.dumps(event_info)



if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
