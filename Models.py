"""
Define all data models.
# TODO(jwei98): Add convenience methods for adding relationships...
#               Especially for bidirectional relationships, adding one
#               should automatically add the other.
# TODO(jwei98): Add convenience methods around managing the graph.
#               User shouldn't have to do "graph.push" or anything?

# Right now, adding a person, circle, and event looks like this which
# is way too difficult:
# j = Person('Justin', 'justin.test@gmail.com', 'xxx')
# c = Circle('Climbing', 'Group for climbing!')
# j.IsMember.add(c)
# c.HasMember.add(j)
# e = Event('Event', 'event description', 'location', 'time', c)
# c.Scheduled.add(e)
# e.BelongsTo.add(c)
# graph.push(j)
# graph.push(c)
# graph.push(e)

"""
from py2neo.ogm import (GraphObject, Property, Related, RelatedTo, RelatedFrom)


class GraphError(Exception):
    pass


# TODO: Consider __primarykey__ as email rather than implicit __id__
class Person(GraphObject):
    display_name = Property()
    email = Property()
    photo = Property()

    Knows = Related('Person', 'KNOWS')
    IsMember = RelatedTo('Circle', 'IS_MEMBER')
    InvitedTo = Related('Event', 'INVITED_TO')

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

    HasMember = Related('Person', 'HAS_MEMBER')
    Scheduled = Related('Event', 'SCHEDULED')

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

    def json_repr(self):
        return {
            'id': self.__primaryvalue__,
            'display_name': self.display_name,
            'description': self.description,
            'HasMember': [p.__primaryvalue__ for p in list(self.HasMember)],
            'Scheduled': [p.__primaryvalue__ for p in list(self.Scheduled)]
        }


class Event(GraphObject):
    display_name = Property()
    description = Property()
    location = Property()
    start_datetime = Property()
    end_datetime = Property()

    BelongsTo = Related('Circle', 'BELONGS_TO')
    Invited = Related('Person', 'INVITED')

    def __init__(self, display_name, description, location, start_datetime,
                 end_datetime, circle):
        self.display_name = display_name
        self.description = description
        self.location = location
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        # Events should always be linked to a circle.
        self.BelongsTo.add(circle)
        circle.Scheduled.add(self)
        # Each member in the circle should be invited to the event.
        for member in circle.HasMember:
            self.Invited.add(member)
            member.InvitedTo.add(self, properties={'attending': False})

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

    def json_repr(self):
        return {
            'id': self.__primaryvalue__,
            'display_name': self.display_name,
            'description': self.description,
            'location': self.location,
            'start_datetime': self.start_datetime,
            'end_datetime': self.end_datetime,
            'BelongsTo': [p.__primaryvalue__ for p in list(self.BelongsTo)],
            'Invited': [p.__primaryvalue__ for p in list(self.Invited)]
        }
