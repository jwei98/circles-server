"""
Library for functions related to cypher queries.
"""
from enum import Enum
from string import Template

# Query Variabes: src, rel, dest
# Inputted Variables: src_id, src_type, rel_type, dest_type, action,
#                     action_entity
GENERIC_QUERY = 'MATCH (src:$src_type)-[rel:$rel_type]-(dest:$dest_type) WHERE ID(src)=$src_id $action $action_entity'


class CypherAction(Enum):
    RETURN = 'RETURN'
    DELETE = 'DELETE'


def one_hop_from_id(graph, src_id, src_type, rel_type, dest_type,
                    action_entity):
    """Returns list of matches. Each match is a dictionary with keys being
    the action_entity specified."""
    query = Template(GENERIC_QUERY).substitute(src_type=src_type,
                                               src_id=src_id,
                                               rel_type=rel_type,
                                               dest_type=dest_type,
                                               action=CypherAction.RETURN.name,
                                               action_entity=action_entity)
    matches = graph.run(query).data()
    return matches


def delete_relationships_from(graph, src_id, src_type, rel_type, dest_type):
    """ Deletes relationships of type rel_type connected to node w/ src_id."""
    query = Template(GENERIC_QUERY).substitute(src_type=src_type,
                                               src_id=src_id,
                                               rel_type=rel_type,
                                               dest_type=dest_type,
                                               action=CypherAction.DELETE.name,
                                               action_entity='rel')
    print(query)
    graph.run(query)
