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


class Circle(GraphObject):
    display_name = Property()
    description = Property()

    HasMember = Related('Person', 'HAS_MEMBER')
    Scheduled = Related('Event', 'SCHEDULED')

    def __init__(self, display_name, description):
        self.display_name = display_name
        self.description = description


class Event(GraphObject):
    display_name = Property()
    description = Property()
    location = Property()
    datetime = Property()

    BelongsTo = Related('Circle', 'BELONGS_TO')
    Invited = Related('Person', 'INVITED')

    def __init__(self, display_name, description, location, datetime, circle):
        self.display_name = display_name
        self.description = description
        self.location = location 
        self.datetime = datetime
        # Events should always be linked to a circle.
        self.BelongsTo.add(circle)
        # Each member in the circle should be invited to the event.
        for member in circle.HasMember:
            member.InvitedTo.add(self, properties={'attending': False})

