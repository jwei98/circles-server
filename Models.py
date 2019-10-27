"""
Define all data models.
"""

from py2neo.ogm import (GraphObject, Property, Related, RelatedTo, RelatedFrom)


class Person(GraphObject):
    __primarykey__ = "username"

    # Properties.
    username = Property()
    display_name = Property()
    uid = Property()
    email = Property()
    photo = Property()

    # Relationships.
    Knows = Related("Person", "KNOWS")
    Circles = RelatedTo("Circle", "PART_OF")
    InvitedTo = Related("Event", "INVITED_TO")

    def __init__(self, username, display_name, email, photo):
        self.username = username
        self.display_name = display_name
        self.email = email
        self.photo = photo

class Circle(GraphObject):

    # Properties.

    name = Property()

    # Relationships.
    Contains = Related("Person", "CONTAINS")
    Scheduled = Related("Event", "SCHEDULED")

    def __init__(self, name, members, events):
        self.name = name
        # Initialize ID and Neo relationships

class Event(GraphObject):

    # Properties.

    name = Property()
    description = Property()
    datetime = Property()

    # Relationships.
    InvitedTo = RelatedFrom("Person", "INVITED_TO")
    BelongsTo = Related("Circle", "BELONGS_TO")

    def __init__(self, name, description, time, circle):
        self.name = name
        self.description = description
        self.datetime = time
        # is there a way to initialize the neo relationships

