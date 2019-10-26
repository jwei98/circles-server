"""
Define all data models.
"""

from py2neo.ogm import (GraphObject, Property, Related)


class Person(GraphObject):
    __primarykey__ = "name"

    name = Property()
    age = Property()

    friends = Related("Person", "KNOWS")

    def __init__(self, name, age):
        self.name = name
        self.age = age 

