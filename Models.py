"""
Define all data models.
"""
import string
from collections import defaultdict
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
        self.email = email.lower()
        self.photo = photo

    @classmethod
    def from_json(cls, json, graph, push_updates=False):
        """
        Required json keys:
        - display_name: str
        - email: str
        Optional json:
        - photo: str
        """
        p = cls(json['display_name'], json['email'], json.get('photo'))

        for p_id in json.get('People', []):
            p2 = Person.match(graph, p_id).first()
            if not p2:
                raise GraphError('Person with id %s does not exist.' % p_id)
            p.Knows.add(p2)

        for c_id in json.get('Circles', []):
            c = Circle.match(graph, c_id).first()
            if not c:
                raise GraphError('Person with id %s does not exist.' % c_id)
            p.IsMember.add(c)

        for c_id, events in json.get('Events', {}).items():
            for e_id, is_attending in events.items():
                e = Event.match(graph, int(e_id)).first()
                p.InvitedTo.add(e, properties={'attending': is_attending})

        if push_updates:
            graph.push(p)

        return p

    def update_to(self, graph, other_person):
        self.display_name = other_person.display_name
        self.email = other_person.email.lower()
        self.photo = other_person.photo

        self.Knows.clear()
        for p in other_person.Knows:
            self.Knows.add(p)

        self.IsMember.clear()
        for c in other_person.IsMember:
            self.IsMember.add(c)

        self.InvitedTo.clear()
        for e in other_person.InvitedTo:
            is_attending = other_person.InvitedTo.get(e, 'attending')
            self.InvitedTo.add(e, properties={'attending': is_attending})

        graph.push(self)
        return self

    def delete(self, graph):
        cypher.delete_node(self, graph)

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

    def json_repr(self, graph):
        events = defaultdict(dict)
        for e in self.InvitedTo:
            is_attending = self.InvitedTo.get(e, 'attending')
            events[str(e.circle_id)][str(e.__primaryvalue__)] = is_attending
        return {
            'id': self.__primaryvalue__,
            'display_name': self.display_name,
            'email': self.email,
            'photo': self.photo,
            'People': [p.__primaryvalue__ for p in list(self.Knows)],
            'Circles': [c.__primaryvalue__ for c in list(self.IsMember)],
            'Events': events
        }

    def json_repr_lim(self):
        return{
            'id': self.__primaryvalue__,
            'display_name': self.display_name,
            'photo': self.photo,
        }

    def json_repr_lim(self):
        return{
            'id': self.__primaryvalue__,
            'display_name': self.display_name,
            'photo': self.photo,
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
            c.Scheduled.add(e)

        # Push all updates to remote graph.
        if push_updates:
            for p in c.members:
                p.IsMember.add(c)
                graph.push(p)
            graph.push(c)

        return c

    def delete(self, graph):
        # Delete all related events first.
        for e in self.Scheduled:
            cypher.delete_node(e, graph)
        cypher.delete_node(self, graph)

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
        self.Scheduled.clear()
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
    circle_id = Property()

    def __init__(self, display_name, description, location, start_datetime,
                 end_datetime, owner_id, circle_id):
        self.display_name = display_name
        self.description = description
        self.location = location
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.created_at = datetime.utcnow().replace(microsecond=0).isoformat()
        self.owner_id = owner_id
        self.circle_id = circle_id

        self.invitees = []  # [(p_id, boolean)...]
        self.circle = None

    @classmethod
    def from_json(cls, json, graph, push_updates=False):
        # Specified Circle must exist.
        c_id = json['Circle']
        c = Circle.match(graph, c_id).first()
        if not c:
            raise GraphError('Event with id %s does not exist.' % c_id)

        e = cls(json['display_name'], json.get('description'),
                json['location'], json['start_datetime'],
                json['end_datetime'], json['owner_id'], c_id)
        e.circle = c

        # Add invitees to circle (safe if no 'People' field).
        for p_id, is_attending in json.get('People', {}).items():
            p_id = int(p_id)
            p = Person.match(graph, p_id).first()
            if not p:
                raise GraphError('Person with id %s does not exist.' % p_id)
            e.invitees.append((p, is_attending))

        # Push all related updates to remote graph.
        if push_updates:
            for p, is_attending in e.invitees:
                p.InvitedTo.add(e, {'attending': is_attending})
                graph.push(p)
            c.Scheduled.add(e)
            graph.push(c)
            graph.push(e)

        return e

    def update_to(self, graph, to_event):
        """Updates self to have same properties as to_event."""
        self.display_name = to_event.display_name
        self.description = to_event.description
        self.location = to_event.location
        self.start_datetime = to_event.start_datetime
        self.end_datetime = to_event.end_datetime
        self.created_at = to_event.created_at
        self.owner_id = to_event.owner_id
        self.circle_id = to_event.circle_id

        # Update members.
        cypher.delete_relationships_from(graph, self.__primaryvalue__,
                                         'Event', 'INVITED_TO', 'Person')
        # Update associated circle.
        cypher.delete_relationships_from(graph, self.__primaryvalue__,
                                         'Event', 'SCHEDULED', 'Circle')

        for p, is_attending in to_event.invitees:
            p.InvitedTo.add(self, {'attending': is_attending})
            graph.push(p)
        to_event.circle.Scheduled.add(self)
        graph.push(to_event.circle)

        graph.push(self)
        return self

    def delete(self, graph):
        cypher.delete_node(self, graph)

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
            'circle_name': circles[0].display_name,
            'People':
            {p.__primaryvalue__: attending
             for p, attending in invitees}
        }
