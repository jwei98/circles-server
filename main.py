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


@app.route('/circles/api/v1.0/users/<int:person_id>/', defaults={'resource': None})
@app.route('/circles/api/v1.0/users/<int:person_id>/<resource>', methods=['GET'])
def get_person(person_id, resource):
    # Request all users.
    if not person_id:
        return jsonify(Person=get_all_nodes(Person))
    # Fetch the person
    person = Person.match(graph, person_id).first()
    if not person:
        abort(404, description="Resource not found")
    if not resource:
        # Request specific user.
        return jsonify(Person=person.json_repr())

    # Request specific resource associated with the person
    output = []
    if resource not in ['circles', 'events', 'knows']:
        abort(404, description="Invalid resource specified")

    if resource == 'circles':
        for c in person.IsMember:
            output.append(c.json_repr())
    if resource == 'events':
        for e in person.InvitedTo:
            output.append(e.json_repr())
    if resource == 'knows':
        for k in person.Knows:
            output.append(k.json_repr())
    return jsonify(output)


@app.route('/circles/api/v1.0/circles/<int:circle_id>/', defaults={'resource': None})
@app.route('/circles/api/v1.0/circles/<int:circle_id>/<resource>', methods=['GET'])
def get_circle(circle_id, resource):
    # Request all circles.
    if not circle_id:
        return jsonify(Circle=get_all_nodes(Circle))

    # Fetch circle.
    circle = Circle.match(graph, circle_id).first()
    if not circle:
        abort(404, description="Resource not found")
    if not resource:
        # Request specific circle
        return jsonify(Circle=circle.json_repr())

    # Request specific resource associated with the circle
    output = []
    if resource not in ['members', 'events']:
        abort(404, description="Invalid resource specified")

    if resource == 'members':
        for m in circle.HasMember:
            output.append(m.json_repr())
    if resource == 'events':
        for e in circle.Scheduled:
            output.append(e.json_repr())
    return jsonify(output)


@app.route('/circles/api/v1.0/events/<int:event_id>/', defaults={'resource': None})
@app.route('/circles/api/v1.0/events/<int:event_id>/<resource>', methods=['GET'])
def get_event(event_id, resource):
    # Request all events.
    if not event_id:
        return jsonify(Event=get_all_nodes(Event))

    # Fetch event.
    event = Event.match(graph, event_id).first()
    if not event:
        abort(404, description="Resource not found")
    if not resource:
        # Request specific event.
        return jsonify(Event=event.json_repr())

        # Request specific resource associated with the circle
    output = []
    if resource not in ['invitees', 'circle']:
        abort(404, description="Invalid resource specified")

    if resource == 'circle':
        for c in event.BelongsTo:
            output.append(c.json_repr())
    if resource == 'invitees':
        for p in event.Invited:
            output.append(p.json_repr())
    return jsonify(output)


@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
