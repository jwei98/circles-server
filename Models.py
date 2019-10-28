"""
Define all data models.
"""

from py2neo.ogm import (GraphObject, Property, Related, RelatedTo, RelatedFrom)


class Person(GraphObject):
    display_name = Property()
    email = Property()
    photo = Property()

    Knows = Related("Person", "KNOWS")
    IsMember = RelatedTo("Circle", "IS_MEMBER")
    InvitedTo = Related("Event", "INVITED_TO")

    def __init__(self, display_name, email, photo):
        self.display_name = display_name
        self.email = email
        self.photo = photo


class Circle(GraphObject):
    display_name = Property()
    description = Property()

    HasMember = Related("Person", "HAS_MEMBER")
    Scheduled = Related("Event", "SCHEDULED")

    def __init__(self, display_name, description):
        self.display_name = display_name
        self.description = description


class Event(GraphObject):
    display_name = Property()
    description = Property()
    location = Property()
    datetime = Property()

    BelongsTo = Related("Circle", "BELONGS_TO")
    Invited = Related("Person", "INVITED")
    # TODO: How do we add a property to an edge? i.e. the boolean for RSVP

    def __init__(self, display_name, description, location, datetime, circle):
        self.display_name = display_name
        self.description = description
        self.location = location 
        self.datetime = datetime
        # Events should always be linked to a circle.
        self.BelongsTo.add(circle)
        # Each member in the circle an event is attached to should be invited.
        for guest in circle.HasMember:
            self.Invited.add(guest)

