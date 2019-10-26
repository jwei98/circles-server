"""
Define all data models.
"""

from py2neo.ogm import (GraphObject, Property, Related)


class Person(GraphObject):
    __primarykey__ = "name"

    # Properties.
    username = Property()
    display_name = Property()
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

