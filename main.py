"""
Main driver for Flask server.
"""
import os
import json

from flask import (Flask, abort, jsonify, render_template)
from py2neo import Graph

import auth
from Models import Person, Circle, Event

app = Flask(__name__)

# Connect to Neo4j graph.
host, username, password = auth.neo4j_creds()
graph = Graph(host=host, username=username, password=password, secure=True)


def get_all_nodes(graph_cls):
    """Gets all nodes of a certain GraphObject type from graph, e.g. Person"""
    nodes = []
    for obj in list(graph_cls.match(graph)):
        nodes.append(obj.json_repr())
    return nodes


@app.route('/')
def hello():
    return 'Hello, Circles!!'


@app.route('/circles/api/v1.0/users/', defaults={'person_id': None})
@app.route('/circles/api/v1.0/users/<int:person_id>', methods=['GET'])
def get_person(person_id):
    # Request all users.
    if not person_id:
        return jsonify(Person=get_all_nodes(Person))

    # Request specific user.
    person = Person.match(graph, person_id).first()
    if not person:
        abort(404, description="Resource not found")
    return jsonify(Person=person.json_repr())


@app.route('/circles/api/v1.0/users/<int:person_id>/circles', methods=['GET'])
def get_person_circles(person_id):
    if not person_id:
        return get_circle(None)
    person = Person.match(graph, person_id).first()
    if not person:
        abort(404, description="resource not found")
    output = []
    for c in person.IsMember:
        output.append(c.json_repr())
    return jsonify(output)


@app.route('/circles/api/v1.0/users/<int:person_id>/events', methods=['GET'])
def get_person_circles(person_id):
    if not person_id:
        return get_event(None)
    person = Person.match(graph, person_id).first()
    if not person:
        abort(404, description="resource not found")
    output = []
    for e in person.InvitedTo:
        output.append(e.json_repr())
    return jsonify(output)


@app.route('/circles/api/v1.0/circles/', defaults={'circle_id': None})
@app.route('/circles/api/v1.0/circles/<int:circle_id>', methods=['GET'])
def get_circle(circle_id):
    # Request all circles.
    if not circle_id:
        return jsonify(Circle=get_all_nodes(Circle))

    # Request specific circle.
    circle = Circle.match(graph, circle_id).first()
    if not circle:
        abort(404, description="Resource not found")
    return jsonify(Circle=circle.json_repr())


@app.route('/circles/api/v1.0/events/', defaults={'event_id': None})
@app.route('/circles/api/v1.0/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    # Request all events.
    if not event_id:
        return jsonify(Event=get_all_nodes(Event))

    # Request specific event.
    event = Event.match(graph, event_id).first()
    if not event:
        abort(404, description="Resource not found")
    return jsonify(Event=event.json_repr())


@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
