"""
Main driver for Flask server.
"""
import os
import json
from itertools import combinations

from flask import (Flask, abort, jsonify, render_template, request)
from py2neo import Graph

import auth
from Models import Person, Circle, Event

KNOWS = 'knows'
MEMBERS = 'members'
INVITEES = 'invitees'
CIRCLES = 'circles'
CIRCLE = 'circle'
EVENTS = 'events'
SUCCESS_JSON = json.dumps({'success': True}), 200, {
    'ContentType': 'application/json'
}

app = Flask(__name__)

# Connect to Neo4j graph.
host, username, password = auth.neo4j_creds()
graph = Graph(host=host, username=username, password=password, secure=True)
"""
GET routes.
"""
@app.route('/circles/api/v1.0/users/<int:person_id>/',
           defaults={'resource': None})
@app.route('/circles/api/v1.0/users/<int:person_id>/<resource>',
           methods=['GET'])
def get_person(person_id, resource):
    # Fetch the person
    person = Person.match(graph, person_id).first()
    if not person:
        abort(404, description='Resource not found')
    if not resource:
        # Request specific user.
        return jsonify(person.json_repr(graph))

    # Request specific resource associated with the person
    if resource not in [CIRCLES, EVENTS, KNOWS]:
        abort(404, description='Invalid resource specified')

    elif resource == CIRCLES:
        return jsonify([c.json_repr(graph) for c in person.IsMember])
    elif resource == EVENTS:
        return jsonify([e.json_repr(graph) for e in person.InvitedTo])
    elif resource == KNOWS:
        return jsonify([k.json_repr(graph) for k in person.Knows])


@app.route('/circles/api/v1.0/circles/<int:circle_id>/',
           defaults={'resource': None})
@app.route('/circles/api/v1.0/circles/<int:circle_id>/<resource>',
           methods=['GET'])
def get_circle(circle_id, resource):

    # Fetch circle.
    circle = Circle.match(graph, circle_id).first()
    if not circle:
        abort(404, description='Resource not found')
    if not resource:
        # Request specific circle
        return jsonify(circle.json_repr(graph))

    # Request specific resource associated with the circle
    if resource not in [MEMBERS, EVENTS]:
        abort(404, description='Invalid resource specified')
    elif resource == MEMBERS:
        return jsonify(
            [m.json_repr(graph) for m in Circle.members_of(graph, circle_id)])
    elif resource == EVENTS:
        return jsonify([e.json_repr(graph) for e in circle.Scheduled])


@app.route('/circles/api/v1.0/events/<int:event_id>/',
           defaults={'resource': None})
@app.route('/circles/api/v1.0/events/<int:event_id>/<resource>',
           methods=['GET'])
def get_event(event_id, resource):
    # Fetch event.
    event = Event.match(graph, event_id).first()
    if not event:
        abort(404, description='Resource not found')
    if not resource:
        # Request specific event.
        return jsonify(event.json_repr(graph))

        # Request specific resource associated with the circle
    if resource not in [INVITEES, CIRCLE]:
        abort(404, description='Invalid resource specified')

    elif resource == CIRCLE:
        return jsonify(
            list(event.circles_of(graph, event_id))[0].json_repr(graph))
    elif resource == INVITEES:
        return event.json_repr(graph)['People']


"""
POST routes.
"""
@app.route('/circles/api/v1.0/circles', methods=['POST'])
def post_circle():
    """
    Required json keys:
    - display_name: String
    - People: [<int>, <int>, ..., <int>]
    Optional keys:
    - description: String
    """
    req_json = request.get_json()
    try:
        c = Circle.from_json(req_json)
        # Make queries for actual Person objects given their id's.
        members = [
            Person.match(graph, p_id).first() for p_id in req_json['People']
        ]

        # Add all members to circle.
        for i, p in enumerate(members):
            if not p:
                bad_request(
                    'Attempted to add person with id %s who does not exist.' %
                    req_json['People'][i])
            p.IsMember.add(c)
            # If we don't push changes here, they'll get overwritten later.
            graph.push(p)

        # Everyone in circle should 'know' each other.
        for p1, p2 in combinations(members, 2):
            # We need to pull so we don't overwrite earlier transactions.
            graph.pull(p1)
            p1.Knows.add(p2)
            graph.push(p1)

        graph.push(c)

        return SUCCESS_JSON
    # KeyErrors will be thrown if any required JSON fields are not present.
    except KeyError as e:
        bad_request('Request JSON must include key %s' % e)


@app.route('/circles/api/v1.0/events', methods=['POST'])
def post_event():
    """
    Required json keys:
    - display_name: String
    - location: String
    - start_datetime: <datetime>
    - end_datetime: <datetime>
    - Circle: <int>
    Optional keys:
    - description: String
    """
    req_json = request.get_json()
    try:
        # Circle must exist to create event.
        c = Circle.match(graph, req_json['Circle']).first()
        if not c:
            bad_request('Circle %s does not exist.' % req_json['Circle'])

        # Event belongs to a circle.
        e = Event.from_json(req_json)
        c.Scheduled.add(e)

        # Invite all members of circle to event.
        members = Circle.members_of(graph, req_json['Circle'])
        for p in members:
            p.InvitedTo.add(e, properties={'attending': False})
            graph.push(p)

        graph.push(c)
        graph.push(e)

        return SUCCESS_JSON
    except KeyError as e:
        bad_request('Request JSON must include key %s' % e)


"""
Other.
"""
@app.route('/')
def hello():
    return 'Hello, Circles!!'


@app.errorhandler(400)
@app.errorhandler(404)
def error(e):
    return jsonify(error=str(e))


def bad_request(msg):
    abort(400, description=msg)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
