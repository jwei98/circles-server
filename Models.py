"""
Define all data models.
"""

from py2neo.ogm import (GraphObject, Property, Related, RelatedTo, RelatedFrom)


class Person(GraphObject):
    __primarykey__ = "username"

    username = Property()
    display_name = Property()
    uid = Property()
    email = Property()
    photo = Property()

    Knows = Related("Person", "KNOWS")
    Circles = RelatedTo("Circle", "PART_OF")
    InvitedTo = Related("Event", "INVITED_TO")

    def __init__(self, username, display_name, email, photo):
        self.username = username
        self.display_name = display_name
        self.email = email
        self.photo = photo


class Circle(GraphObject):

    name = Property()
    description = Property()

    Contains = Related("Person", "CONTAINS")
    Scheduled = Related("Event", "SCHEDULED")

    def __init__(self, name, description):
        self.name = name


class Event(GraphObject):

    name = Property()
    description = Property()
    datetime = Property()

    InvitedTo = RelatedFrom("Person", "INVITED_TO")
    BelongsTo = Related("Circle", "BELONGS_TO")

    def __init__(self, name, description, time, circle):
        self.name = name
        self.description = description
        self.datetime = time
        # Events should always be linked to a circle.
        self.BelongsTo.add(circle)

