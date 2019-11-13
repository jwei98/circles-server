"""
Main driver for Flask server.
"""
import os
import json

from flask import (Flask, abort, jsonify, request, render_template)
from py2neo import Graph

import auth
from Models import Person, Circle, Event

KNOWS = 'knows'
MEMBERS = 'members'
INVITEES = 'invitees'
CIRCLES = 'circles'
CIRCLE = 'circle'
EVENTS = 'events'

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
@app.route('/circles/api/v1.0/users/<int:person_id>/<resource>', methods=['GET', 'POST'])
def get_person(person_id, resource):
    if request.method == 'PUT':
        content = request.get_json()
        dn = content['display_name']
        email = content['email']
        photo = content['photo']
        newPerson = Person(dn, email, photo)
        for i in content['Knows']:
            newPerson.Knows.add(i)
        for i in content['IsMember']:
            newPerson.IsMember.add(i)
        for i in content['InvitedTo']:
            newPerson.InvitedTo.add(i)
        graph.push(newPerson)
    if request.method == 'GET':
        # Fetch the person
        person = Person.match(graph, person_id).first()
        if not person:
            abort(404, description='Resource not found')
        if not resource:
            # Request specific user.
            return jsonify(person.json_repr())

        # Request specific resource associated with the person
        if resource not in [CIRCLES, EVENTS, KNOWS]:
            abort(404, description='Invalid resource specified')

        elif resource == CIRCLES:
            return jsonify([c.json_repr() for c in person.IsMember])
        elif resource == EVENTS:
            return jsonify([e.json_repr() for e in person.InvitedTo])
        elif resource == KNOWS:
            return jsonify([k.json_repr() for k in person.Knows])


@app.route('/circles/api/v1.0/circles/<int:circle_id>/', defaults={'resource': None})
@app.route('/circles/api/v1.0/circles/<int:circle_id>/<resource>', methods=['GET'])
def get_circle(circle_id, resource):
    # Fetch circle.
    circle = Circle.match(graph, circle_id).first()
    if not circle:
        abort(404, description='Resource not found')
    if not resource:
        # Request specific circle
        return jsonify(circle.json_repr())

    # Request specific resource associated with the circle
    if resource not in [MEMBERS, EVENTS]:
        abort(404, description='Invalid resource specified')

    elif resource == MEMBERS:
        return jsonify([m.json_repr() for m in circle.HasMember])
    elif resource == EVENTS:
        return jsonify([e.json_repr() for e in circle.Scheduled])


@app.route('/circles/api/v1.0/events/<int:event_id>/', defaults={'resource': None})
@app.route('/circles/api/v1.0/events/<int:event_id>/<resource>', methods=['GET'])
def get_event(event_id, resource):
    # Fetch event.
    event = Event.match(graph, event_id).first()
    if not event:
        abort(404, description='Resource not found')
    if not resource:
        # Request specific event.
        return jsonify(event.json_repr())

        # Request specific resource associated with the circle
    if resource not in [INVITEES, CIRCLE]:
        abort(404, description='Invalid resource specified')

    elif resource == CIRCLE:
        return jsonify(list(event.BelongsTo)[0].json_repr())
    elif resource == INVITEES:
        rsvp = {}
        for p in event.Invited:
            rsvp[p.__primaryvalue__] = p.InvitedTo.get(event, 'attending')
        return jsonify(rsvp)


@app.errorhandler(404)
def resource_not_found(e):
    return jsonify(error=str(e)), 404


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
