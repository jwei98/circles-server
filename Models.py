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
from string import Template
from py2neo.ogm import (GraphObject, Property, Related, RelatedTo, RelatedFrom)

# Given a source node's id and type, generates query to retrieve a list of all
# nodes that connect to this source node through a particular relationship type
# `r_type`. For convenience, this query searches edges bidirectionally.
ONE_HOP = 'MATCH (src:$src_type)-[r:$r_type]-(match:$match_type) WHERE ID(src)=$src_id RETURN ID(match)'


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

    def json_repr(self):
        return {
            'id': self.__primaryvalue__,
            'display_name': self.display_name,
            'email': self.email,
            'photo': self.photo,
            'Knows': [p.__primaryvalue__ for p in list(self.Knows)],
            'IsMember': [p.__primaryvalue__ for p in list(self.IsMember)],
            'InvitedTo': [p.__primaryvalue__ for p in list(self.InvitedTo)]
        }


class Circle(GraphObject):
    display_name = Property()
    description = Property()

    Scheduled = RelatedTo('Event', 'SCHEDULED')

    def __init__(self, display_name, description):
        self.display_name = display_name
        self.description = description

    @classmethod
    def from_json(cls, json, graph):
        """
        Required json keys:
        - display_name
        Optional keys:
        - description
        - HasMember
        """
        c = cls(json['display_name'], json.get('description'))
        for p_id in json.get('HasMember'):
            p = Person.match(graph, p_id).first()
            if not p:
                raise GraphError('Person with id %s not found in graph.' %
                                 p_id)
            c.HasMember.add(p)
        return c

    @staticmethod
    def members_of(graph, circle_id):
        query = Template(ONE_HOP + ', r.attending').substitute(
            src_type='Circle',
            src_id=circle_id,
            r_type='IS_MEMBER',
            match_type='Person')
        matches = graph.run(query).data()
        return [Person.match(graph, m['ID(match)']).first() for m in matches]

    def json_repr(self, graph):
        members = Circle.members_of(graph, self.__primaryvalue__)
        return {
            'id': self.__primaryvalue__,
            'display_name': self.display_name,
            'description': self.description,
            'HasMember': [p.__primaryvalue__ for p in members],
            'Scheduled': [e.__primaryvalue__ for e in list(self.Scheduled)]
        }


class Event(GraphObject):
    display_name = Property()
    description = Property()
    location = Property()
    start_datetime = Property()
    end_datetime = Property()

    def __init__(self, display_name, description, location, start_datetime,
                 end_datetime, circle, graph):
        # TODO: Passing in graph here is SO gross. Please fix.
        self.display_name = display_name
        self.description = description
        self.location = location
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        # Events should always be linked to a circle.
        circle.Scheduled.add(self)
        # Each member in the circle should be invited to the event.
        for member in Circle.members_of(graph, circle.__primaryvalue__):
            member.InvitedTo.add(self, properties={'attending': False})
            graph.push(member)
        graph.push(circle)
        graph.push(self)

    @classmethod
    def from_json(cls, json, graph):
        """
        Required json keys:
        - display_name
        - location
        - start_datetime
        - end_datetime
        - circle_id
        Optional keys:
        - description
        """
        c = Circle.match(graph, json['circle_id']).first()
        if not c:
            raise GraphError('Circle %s does not exist.' % json['circle_id'])
        return cls(json['display_name'], json.get('description'),
                   json['location'], json['start_datetime'],
                   json['end_datetime'], c)

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
        # TODO: Should events be limited to a single Circle?
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
            'BelongsTo': [c.__primaryvalue__ for c in circles],
            'Invited':
            {p.__primaryvalue__: attending
             for p, attending in invitees}
        }
