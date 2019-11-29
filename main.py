"""
Main driver for Flask server.
"""
import os
import json
from itertools import combinations

import auth
from flask import (Flask, abort, jsonify, render_template, request)
from py2neo import Graph

from Models import Person, Circle, Event, GraphError

CIRCLES = 'circles'
CIRCLE = 'circle'
EVENTS = 'events'
PEOPLE = 'people'
SUCCESS_JSON = json.dumps({'success': True}), 200, {
    'ContentType': 'application/json'
}

app = Flask(__name__)

# Connect to Neo4j graph.
host, username, password = auth.neo4j_creds()
graph = Graph(host=host, username=username, password=password, secure=True)
"""
GET and PUT routes.
"""
@app.route('/circles/api/v1.0/users/<int:person_id>', methods=['GET', 'PUT'])
@app.route('/circles/api/v1.0/users/<int:person_id>/<resource>',
           methods=['GET'])
def person(person_id, resource=None):
    # Fetch the person
    person = Person.match(graph, person_id).first()
    if not person:
        abort(404, description='Resource not found')
    if request.method == 'GET':
        if not resource:
            return jsonify(person.json_repr(graph))
        # Request specific resource associated with the person
        if resource == CIRCLES:
            return jsonify([c.json_repr(graph) for c in person.IsMember])
        elif resource == EVENTS:
            return jsonify([e.json_repr(graph) for e in person.InvitedTo])
        elif resource == PEOPLE:
            return jsonify([k.json_repr(graph) for k in person.Knows])
        abort(404, description='Invalid resource specified')
    elif request.method == 'PUT':
        req_json = request.get_json()
        try:
            p = Person.from_json(req_json, graph, push_updates=False)
            person.update_to(graph, p)
            return SUCCESS_JSON
        except KeyError as e:
            bad_request('Request JSON must include key %s' % e)
        except GraphError as e:
            bad_request(e)


@app.route('/circles/api/v1.0/circles/<int:circle_id>', methods=['GET', 'PUT'])
@app.route('/circles/api/v1.0/circles/<int:circle_id>/<resource>',
           methods=['GET'])
def circle(circle_id, resource=None):
    # Fetch circle.
    circle = Circle.match(graph, circle_id).first()
    if not circle:
        abort(404, description='Resource not found')
    if request.method == 'GET':
        if not resource:
            # Request specific circle
            return jsonify(circle.json_repr(graph))

        # Request specific resource associated with the circle
        if resource == PEOPLE:
            return jsonify([
                m.json_repr(graph)
                for m in Circle.members_of(graph, circle_id)
            ])
        elif resource == EVENTS:
            return jsonify([e.json_repr(graph) for e in circle.Scheduled])
        abort(404, description='Invalid resource specified')
    elif request.method == 'PUT':
        req_json = request.get_json()
        try:
            c = Circle.from_json(req_json, graph, push_updates=False)
            circle.update_to(graph, c)
            return SUCCESS_JSON
        # KeyErrors will be thrown if any required JSON fields are not present.
        except KeyError as e:
            bad_request('Request JSON must include key %s' % e)
        except GraphError as e:
            bad_request(e)


@app.route('/circles/api/v1.0/events/<int:event_id>', methods=['GET', 'PUT'])
@app.route('/circles/api/v1.0/events/<int:event_id>/<resource>', methods=['GET'])
def event(event_id, resource=None):
    # Fetch event.
    event = Event.match(graph, event_id).first()
    if not event:
        abort(404, description='Resource not found')
    if request.method == 'GET':
        if not resource:
            # Request specific event.
            return jsonify(event.json_repr(graph))

            # Request specific resource associated with the circle
        if resource in [CIRCLE, CIRCLES]:
            return jsonify(
                list(event.circles_of(graph, event_id))[0].json_repr(graph))
        elif resource == PEOPLE:
            return event.json_repr(graph)['People']
        abort(404, description='Invalid resource specified')
    elif request.method == 'PUT':
        try:
            req_json = request.get_json()
            e = Event.from_json(req_json, graph, push_updates=False)
            event.update_to(graph, e)
            return SUCCESS_JSON
        except KeyError as e:
            bad_request('Request JSON must include key %s' % e)
        except GraphError as e:
            bad_request(e)


"""
POST routes.
"""
@app.route('/circles/api/v1.0/users', methods=['POST'])
def post_user():
    """
       Required json keys:
       - display_name: String
       - Email: String
       Optional json key:
       - Photo: String
       """
    req_json = request.get_json()
    try:
        p = Person.from_json(req_json, graph, push_updates=True)
        return SUCCESS_JSON
    except KeyError as e:
        bad_request('Request JSON must include key %s' % e)


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
        c = Circle.from_json(req_json, graph, push_updates=True)
        return SUCCESS_JSON
    # KeyErrors will be thrown if any required JSON fields are not present.
    except KeyError as e:
        bad_request('Request JSON must include key %s' % e)
    except GraphError as e:
        bad_request(e)


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
    # TODO: Using auth, check if Person posting event is owner of Circle.
    req_json = request.get_json()
    try:
        e = Event.from_json(req_json, graph, push_updates=True)
        return SUCCESS_JSON
    except KeyError as e:
        bad_request('Request JSON must include key %s' % e)
    except GraphError as e:
        bad_request(e)


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
