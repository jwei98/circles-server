"""
Library for functions related to cypher queries.
"""
from enum import Enum
from string import Template


def construct_query(src_type='', src_id='', rel_type='', dest_type='',
                    action='RETURN', action_entity='ID(dest)'):
    if src_type:
        src_type = ':' + src_type
    if rel_type:
        rel_type = ':' + rel_type
    if dest_type:
        dest_type = ':' + dest_type
    query = Template('MATCH (src$src_type)-[rel$rel_type]-(dest$dest_type) WHERE ID(src)=$src_id $action $action_entity').substitute(
        src_type=src_type, rel_type=rel_type, dest_type=dest_type,
        src_id=src_id, action=action, action_entity=action_entity)
    return query


def one_hop_from_id(graph, src_id, src_type, rel_type, dest_type,
                    action_entity):
    """Returns list of matches. Each match is a dictionary with keys being
    the action_entity specified."""
    query = construct_query(src_type=src_type, src_id=src_id,
                            rel_type=rel_type, dest_type=dest_type,
                            action_entity=action_entity)
    matches = graph.run(query).data()
    return matches


def delete_relationships_from(graph, src_id, src_type=None, rel_type=None,
                              dest_type=None):
    """ Deletes relationships of type rel_type connected to node w/ src_id."""
    query = construct_query(src_type=src_type, src_id=src_id,
                            rel_type=rel_type, dest_type=dest_type,
                            action='DELETE', action_entity='rel')
    graph.run(query)


def delete_node(node, graph):
    """ Deletes a node and all its relationships from graph."""
    src_type = type(node).__name__
    src_id = node.__primaryvalue__

    # Delete all relationships.
    delete_rels_query = construct_query(src_type=src_type, src_id=src_id,
                                        action='DELETE', action_entity='rel')
    # Delete node itself.
    delete_node_query = Template(
        'MATCH(src: $src_type) WHERE ID(src)=$src_id DELETE src'
    ).substitute(src_type=src_type, src_id=src_id)

    graph.run(delete_rels_query)
    graph.run(delete_node_query)
