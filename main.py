"""
Main driver for Flask server.
"""
import os
import json
from itertools import combinations
import firebase_admin
from firebase_admin import credentials, auth as fb_auth, _auth_utils as a_util
firebase_admin.initialize_app()

import auth
from pyfcm import FCMNotification
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

# Setup push notifications
push_service = FCMNotification(api_key=auth.fcm_creds())

# Connect to Neo4j graph.
host, username, password = auth.neo4j_creds()
graph = Graph(host=host, username=username,
              password=password, secure=True)



def auth_get_req_user(request):
    # Fetch the person making the request
    req_token = request.headers.get('Authorization')
    try:
        decoded_token = fb_auth.verify_id_token(req_token)
        req_email = decoded_token['email']
        req_user = (Person.match(graph).where("_.email = '{}'".format(req_email))).first()
        return req_user
    except a_util.InvalidIdTokenError:
        bad_request('Invalid authorization attempt.')


"""
GET, PUT, and DELETE routes.
"""
@app.route('/circles/api/v1.0/users/<int:person_id>', methods=['GET', 'PUT',
                                                               'DELETE'])
@app.route('/circles/api/v1.0/users/<int:person_id>/<resource>',
           methods=['GET'])
def person(person_id, resource=None):
    # Fetch the person making the request
    req_user = auth_get_req_user(request)
    # Fetch the person requested
    person = Person.match(graph, person_id).first()
    if not person:
        abort(404, description='Resource not found')
    # Determine if a user is requesting their own data
    self_req = req_user.__primaryvalue__ == person.__primaryvalue__
    if request.method == 'GET':
        if not resource:
            if self_req:
                return jsonify(person.json_repr(graph))
            else:
                return jsonify(person.json_repr_lim())
        # Request specific resource associated with the person if they are authorized
        if self_req:
            if resource == CIRCLES:
                return jsonify([c.json_repr(graph) for c in person.IsMember])
            elif resource == EVENTS:
                return jsonify([e.json_repr(graph) for e in person.InvitedTo])
            elif resource == PEOPLE:
                return jsonify([k.json_repr_lim() for k in person.Knows])
            abort(404, description='Invalid resource specified')
        abort(403, description='Unauthorized resource access')

    elif request.method == 'PUT':
        if self_req:
            req_json = request.get_json()
            try:
                p = Person.from_json(req_json, graph, push_updates=False)
                person.update_to(graph, p)
                return SUCCESS_JSON
            except KeyError as e:
                bad_request('Request JSON must include key %s' % e)
            except GraphError as e:
                bad_request(e)
        abort(403, description='Unauthorized modification request')

    elif request.method == 'DELETE':
        if self_req:
            person.delete(graph)
            return SUCCESS_JSON
        abort(403, description='Unauthorized deletion request')


@app.route('/circles/api/v1.0/circles/<int:circle_id>', methods=['GET', 'PUT',
                                                                 'DELETE'])
@app.route('/circles/api/v1.0/circles/<int:circle_id>/<resource>',
           methods=['GET'])
def circle(circle_id, resource=None):
    # Fetch the person making the request
    req_user = auth_get_req_user(request)
    # Fetch circle being requested.
    circle = Circle.match(graph, circle_id).first()
    if not circle:
        abort(404, description='Resource not found')
    # Determine if user that is requesting the circle has privilege to see it
    owner_req = req_user.__primaryvalue__ == circle.owner_id
    member_req = circle_id in list(
        c.__primaryvalue__ for c in req_user.IsMember)
    if not member_req:
        abort(403, description='Unauthorized circle get')

    if request.method == 'GET':
        if member_req:
            if not resource:
                # Request specific circle
                return jsonify(circle.json_repr(graph))
            # Request specific resource associated with the circle
            if resource == PEOPLE:
                return jsonify([
                    m.json_repr_lim()
                    for m in Circle.members_of(graph, circle_id)
                ])
            elif resource == EVENTS:
                return jsonify([e.json_repr(graph) for e in circle.Scheduled])
            abort(404, description='Invalid resource specified')
        abort(403, description='Unauthorized circle request')
    elif request.method == 'PUT':
        req_json = request.get_json()
        try:
            c = Circle.from_json(req_json, graph, push_updates=False)

            # TODO: Fix this logic/make it more granular depending on the type of update
            if owner_req or \
                    (member_req and c.members_can_add) or \
                    (member_req and c.members_can_ping):
                circle.update_to(graph, c)
                return SUCCESS_JSON
            abort(403, 'Unauthorized update request')

        # KeyErrors will be thrown if any required JSON fields are not present.
        except KeyError as e:
            bad_request('Request JSON must include key %s' % e)
        except GraphError as e:
            bad_request(e)

    elif request.method == 'DELETE':
        if owner_req:
            abort(403, description='Unauthorized circle request')
        # Only the owner may delete a circle
        circle.delete(graph)
        return SUCCESS_JSON


@app.route('/circles/api/v1.0/events/<int:event_id>', methods=['GET', 'PUT',
                                                               'DELETE'])
@app.route('/circles/api/v1.0/events/<int:event_id>/<resource>', methods=['GET'])
def event(event_id, resource=None):
    # Fetch event.
    event = Event.match(graph, event_id).first()
    if not event:
        abort(404, description='Resource not found')
    # Fetch the person making the request
    req_user = auth_get_req_user(request)
    owner_req = req_user.__primaryvalue__ == event.owner_id
    guest_req = event_id in list(
        e.__primaryvalue__ for e in req_user.InvitedTo)

    if request.method == 'GET':
        if owner_req or guest_req:  # access is authorized
            if not resource:
                # Request specific event.
                    return jsonify(event.json_repr(graph))
                # Request specific resource associated with the event
            if resource in [CIRCLE, CIRCLES]:
                return jsonify(
                    list(event.circles_of(graph, event_id))[0].json_repr(graph))
            elif resource == PEOPLE:
                return event.json_repr(graph)['People']
            abort(404, description='Invalid resource specified')
        abort(403, description='Unauthorized event update')

    elif request.method == 'PUT':
        if owner_req or guest_req:  # access is authorized
            try:
                req_json = request.get_json()
                e = Event.from_json(req_json, graph, push_updates=False)
                event.update_to(graph, e)
                return SUCCESS_JSON
            except KeyError as e:
                bad_request('Request JSON must include key %s' % e)
            except GraphError as e:
                bad_request(e)
        abort(403, description='Unauthorized event request')
    elif request.method == 'DELETE':
        if owner_req:
            event.delete(graph)
            return SUCCESS_JSON
        abort(403, description='Unauthorized event deletion request')


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

    # Fetch the person making the request (not necessary but could help if frontend is currently providing this)

    req_user = auth_get_req_user(request)


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

    # Fetch the person making the request
    req_user = auth_get_req_user(request)
    # Fetch the circle that the request is associated with
    circle = Circle.match(graph, req_json.get('Circle')).first()
    if not circle:
        abort(404, description='Invalid Circle Specified')
    owner_req = req_user.__primaryvalue__ == circle.owner_id
    member_req = circle.__primaryvalue__ in list(
        c.__primaryvalue__ for c in req_user.IsMember)
    member_valid_ping = owner_req or (member_req and circle.members_can_ping)
    if owner_req or member_valid_ping:
        try:
            e = Event.from_json(req_json, graph, push_updates=True)
            return SUCCESS_JSON
        except KeyError as e:
            bad_request('Request JSON must include key %s' % e)
        except GraphError as e:
            bad_request(e)
    abort(403, description='Insufficient Permissions')


"""
Other.
"""
@app.route('/')
def hello():
    # TODO: This is currently hardcoded. Should be stored in a node property.
    registration_id = "cp1AyrAc55w:APA91bGRjsuynQRvAvGVWR2W8EoWSdcxXwGypSkC13VdF6-uGJiOJCDI0bQYjbS-_ex9Xt666tmQINMUTp10ZICsYmrcHZzbAX7ikvkd6T-EjqXBcV-WaAdgeE3SqFIuyGRwU_lbbvbQ"
    message_title = "Uber update"
    message_body = "Hi john, your customized news for today is ready"
    result = push_service.notify_single_device(registration_id=registration_id,
                                               message_title=message_title, message_body=message_body)
    print(result)
    return 'Hello, Circles!!'


@app.route('/circles/api/v1.0/getid')
def getid():
    # Fetch the person making the request
    req_user = auth_get_req_user(request)
    return str(req_user.__primaryvalue__)


@app.errorhandler(400)
@app.errorhandler(404)
def error(e):
    return jsonify(error=str(e))


def bad_request(msg):
    abort(400, description=msg)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
