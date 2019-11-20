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
from string import Template
from py2neo.ogm import (GraphObject, Property, Related, RelatedTo, RelatedFrom)

# Given a source node's id and type, generates query to retrieve a list of all
# nodes that connect to this source node through a particular relationship type
# `r_type`. For convenience, this query searches edges bidirectionally.
ONE_HOP = 'MATCH (src:$src_type)-[r:$r_type]-(match:$match_type) WHERE ID(src)=$src_id RETURN ID(match)'


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
        - display_name
        - email
        Optional json:
        - photo
        """
        c = cls(json['display_name'], json['email'], json.get('photo'))

        return c

    @staticmethod
    def attendance_of(graph, person_id):
        query = Template(ONE_HOP + ', r.attending').substitute(
            src_type='Person',
            src_id=person_id,
            r_type='INVITED_TO',
            match_type='Event')
        matches = graph.run(query).data()
        return {m['ID(match)']: m['r.attending'] for m in matches}

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

    @classmethod
    def from_json(cls, json):
        """
        Required json keys:
        - display_name <str>
        - owner_id <int>: Creator's Person ID.
        Optional keys:
        - description <str>
        - members_can_add <bool>: Whether members can add people to circle.
        - members_can_ping <bool>: Whether members can ping circle.
        """
        # TODO: Check that owner_id is in list of members?
        c = cls(json['display_name'], json.get('description'), json['owner_id'],
                json.get('members_can_add', False),
                json.get('members_can_ping', False))
        return c

    @staticmethod
    def members_of(graph, circle_id):
        query = Template(ONE_HOP).substitute(src_type='Circle',
                                             src_id=circle_id,
                                             r_type='IS_MEMBER',
                                             match_type='Person')
        matches = graph.run(query).data()
        return [Person.match(graph, m['ID(match)']).first() for m in matches]

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
        query = Template(ONE_HOP + ', r.attending').substitute(
            src_type='Event',
            src_id=event_id,
            r_type='INVITED_TO',
            match_type='Person')
        matches = graph.run(query).data()
        return [(Person.match(graph, m['ID(match)']).first(), m['r.attending'])
                for m in matches]

    @staticmethod
    def circles_of(graph, event_id):
        query = Template(ONE_HOP).substitute(src_type='Event',
                                             src_id=event_id,
                                             r_type='SCHEDULED',
                                             match_type='Circle')
        matches = graph.run(query).data()
        return [Circle.match(graph, m['ID(match)']).first() for m in matches]

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
