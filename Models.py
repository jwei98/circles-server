"""
Define all data models.
# TODO(jwei98): Consider caching results instead of making request to Neo4j
                everytime?
# TODO(jwei98): Add convenience methods for adding relationships...
                For example, adding someone to a circle should add KNOWS
                relationships to everyone else in the circle.
# TODO(jwei98): Add convenience methods around managing the graph.
#               User shouldn't have to do "graph.push" or anything?

# Right now, adding a person, circle, and event looks like this which
# is way too difficult:
# j = Person('Justin', 'justin.test@gmail.com', 'xxx')
# c = Circle('Climbing', 'Group for climbing!')
# j.IsMember.add(c)
# e = Event('Event', 'event description', 'location', 'time', c)
# e.BelongsTo.add(c)
# graph.push(j)
# graph.push(c)
# graph.push(e)

"""
from datetime import datetime
from py2neo.ogm import (GraphObject, Property, Related, RelatedTo, RelatedFrom)

import cypher


class GraphError(Exception):
    pass


# TODO: Consider __primarykey__ as email rather than implicit __id__
class Person(GraphObject):
    display_name = Property()
    email = Property()
    photo = Property()

    Knows = Related('Person', 'KNOWS')
    IsMember = RelatedTo('Circle', 'IS_MEMBER')
    InvitedTo = RelatedTo('Event', 'INVITED_TO')

    def __init__(self, display_name, email, photo):
        self.display_name = display_name
        self.email = email
        self.photo = photo

    @classmethod
    def from_json(cls, json):
        """
        Required json keys:
        - display_name: str
        - email: str
        Optional json:
        - photo: str
        """
        return cls(json['display_name'], json['email'], json.get('photo'))

    @staticmethod
    def attendance_of(graph, person_id):
        matches = cypher.one_hop_from_id(
            graph,
            src_id=person_id,
            src_type='Person',
            rel_type='INVITED_TO',
            dest_type='Event',
            action_entity='ID(dest), rel.attending')
        return {m['ID(dest)']: m['rel.attending'] for m in matches}

    def update_from_json(self, json, graph):
        """Replaces an entire node and its relationships with
        given JSON properties."""
        self.display_name = json['display_name']
        self.email = json['email']
        self.photo = json.get('photo')

        # TODO: Handle cases where Person/Circle/Event doesn't exist?
        self.Knows.clear()
        for pid in json.get('People', []):
            p = Person.match(graph, pid).first()
            self.Knows.add(p)

        self.IsMember.clear()
        for cid in json.get('Circles', []):
            c = Circle.match(graph, cid).first()
            self.IsMember.add(c)

        self.InvitedTo.clear()
        # json format: {"Events": {"event_id": <bool>, ...}}
        for eid, is_attending in json.get('Events', {}).items():
            e = Event.match(graph, int(eid)).first()
            self.InvitedTo.add(e, properties={'attending': is_attending})

    def json_repr(self, graph):
        return {
            'id': self.__primaryvalue__,
            'display_name': self.display_name,
            'email': self.email,
            'photo': self.photo,
            'People': [p.__primaryvalue__ for p in list(self.Knows)],
            'Circles': [p.__primaryvalue__ for p in list(self.IsMember)],
            'Events': Person.attendance_of(graph, self.__primaryvalue__)
        }


class Circle(GraphObject):
    display_name = Property()
    description = Property()
    owner_id = Property()
    members_can_add = Property()
    members_can_ping = Property()

    Scheduled = RelatedTo('Event', 'SCHEDULED')

    def __init__(self, display_name, description, owner_id, members_can_add,
                 members_can_ping):
        self.display_name = display_name
        self.description = description
        self.owner_id = owner_id
        self.members_can_add = members_can_add
        self.members_can_ping = members_can_ping
        self.members = []

    @classmethod
    def from_json(cls, json, graph, push_updates=False):
        """
        push_updates: Whether updates should be pushed to graph or not.
                      This should be True if creating a new resource, and
                      false if just using to create a temp object.

        Required json keys:
        - display_name <str>
        - owner_id <int>: Creator's Person ID.
        Optional keys:
        - description <str>
        - members_can_add <bool>: Whether members can add people to circle.
        - members_can_ping <bool>: Whether members can ping circle.
        """
        # TODO: Check that owner_id is in list of members?
        c = cls(json['display_name'], json.get('description'),
                json['owner_id'], json.get('members_can_add', False),
                json.get('members_can_ping', False))

        # Add MEMBERS to circle (safe if no 'People' field).
        for p_id in json.get('People', []):
            p = Person.match(graph, p_id).first()
            if not p:
                raise GraphError('Person with id %s does not exist.' % p_id)
            c.members.append(p)

        # Add EVENTS to circle (safe if no 'Events' field).
        events = []
        for e_id in json.get('Events', []):
            e = Event.match(graph, e_id).first()
            if not e:
                raise GraphError('Event with id %s does not exist.' % e_id)
            events.append(e)
        # Do this only if all events existed.
        for e in events:
            c.Scheduled.add(e)

        # Push all updates to remote graph.
        if push_updates:
            for p in c.members:
                p.IsMember.add(c)
                graph.push(p)
            graph.push(c)

        return c

    @staticmethod
    def members_of(graph, circle_id):
        matches = cypher.one_hop_from_id(graph,
                                         src_id=circle_id,
                                         src_type='Circle',
                                         rel_type='IS_MEMBER',
                                         dest_type='Person',
                                         action_entity='ID(dest)')
        return [Person.match(graph, m['ID(dest)']).first() for m in matches]

    def update_to(self, graph, to_circle):
        """Updates self to have same properties as to_circle."""
        self.display_name = to_circle.display_name
        self.description = to_circle.description
        self.owner_id = to_circle.owner_id
        self.members_can_add = to_circle.members_can_add
        self.members_can_ping = to_circle.members_can_ping

        # Update members.
        cypher.delete_relationships_from(graph, self.__primaryvalue__,
                                         'Circle', 'IS_MEMBER', 'Person')
        # TODO: Should deleting a circle delete all associated events?
        cypher.delete_relationships_from(graph, self.__primaryvalue__,
                                         'Circle', 'SCHEDULED', 'Event')
        for p in to_circle.members:
            p.IsMember.add(self)
            graph.push(p)
        for e in to_circle.Scheduled:
            self.Scheduled.add(e)
        graph.push(self)

        return self

    def json_repr(self, graph):
        members = Circle.members_of(graph, self.__primaryvalue__)
        return {
            'id': self.__primaryvalue__,
            'owner_id': self.owner_id,
            'members_can_add': self.members_can_add,
            'members_can_ping': self.members_can_ping,
            'display_name': self.display_name,
            'description': self.description,
            'People': [p.__primaryvalue__ for p in members],
            'Events': [e.__primaryvalue__ for e in list(self.Scheduled)]
        }


class Event(GraphObject):
    display_name = Property()
    description = Property()
    location = Property()
    start_datetime = Property()
    end_datetime = Property()
    created_at = Property()
    owner_id = Property()

    def __init__(self, display_name, description, location, start_datetime,
                 end_datetime, owner_id):
        self.display_name = display_name
        self.description = description
        self.location = location
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.created_at = datetime.utcnow().replace(microsecond=0).isoformat()
        self.owner_id = owner_id

    @classmethod
    def from_json(cls, json):
        return cls(json['display_name'], json.get('description'),
                   json['location'], json['start_datetime'],
                   json['end_datetime'], json['owner_id'])

    @staticmethod
    def invitees_of(graph, event_id):
        matches = cypher.one_hop_from_id(
            graph,
            src_id=event_id,
            src_type='Event',
            rel_type='INVITED_TO',
            dest_type='Person',
            action_entity='ID(dest), rel.attending')
        return [(Person.match(graph,
                              m['ID(dest)']).first(), m['rel.attending'])
                for m in matches]

    @staticmethod
    def circles_of(graph, event_id):
        matches = cypher.one_hop_from_id(graph,
                                         src_id=event_id,
                                         src_type='Event',
                                         rel_type='SCHEDULED',
                                         dest_type='Circle',
                                         action_entity='ID(dest)')
        return [Circle.match(graph, m['ID(dest)']).first() for m in matches]

    def json_repr(self, graph):
        invitees = Event.invitees_of(graph, self.__primaryvalue__)
        circles = Event.circles_of(graph, self.__primaryvalue__)
        return {
            'id': self.__primaryvalue__,
            'display_name': self.display_name,
            'description': self.description,
            'location': self.location,
            'start_datetime': self.start_datetime,
            'end_datetime': self.end_datetime,
            'created_at': self.created_at,
            'owner_id': self.owner_id,
            'Circle': circles[0].__primaryvalue__,
            'People':
            {p.__primaryvalue__: attending
             for p, attending in invitees}
        }
