#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
model_to_dict() functiion for SQLAlchemy models

Based on answers by "doog abides" and "daveoncode" from 
https://stackoverflow.com/questions/23554119/convert-sqlalchemy-orm-result-to-dict

@author: Hrishikesh Terdalkar
"""

from datetime import datetime

from sqlalchemy.orm import class_mapper

###############################################################################


def model_to_dict(
    obj,
    max_depth: int = 1,
    visited_children: set = None,
    back_relationships: set = None,
):
    """SQLAlchmey objects as python `dict`

    Parameters
    ----------
    obj : SQLAlchemy model object
        Similar to an instance returned by declarative_base()
    max_depth : int, optional
        Maximum depth for recursion on relationships.
        The default is 1.
    visited_children : set, optional
        Set of children already visited.
        The default is None.
        Primary use of this attribute is for recursive calls, and a user
        usually does not explicitly set this.
    back_relationships : set, optional
        Set of back relationships already explored.
        The default is None.
        Primary use of this attribute is for recursive calls, and a user
        usually does not explicitly set this.

    Returns
    -------
    dict
        Python `dict` representation of the SQLAlchemy object
    """
    if visited_children is None:
        visited_children = set()
    if back_relationships is None:
        back_relationships = set()

    mapper = class_mapper(obj.__class__)
    columns = [column.key for column in mapper.columns]
    get_key_value = (
        lambda c: (c, getattr(obj, c).isoformat())
        if isinstance(getattr(obj, c), datetime) else
        (c, getattr(obj, c))
    )
    data = dict(map(get_key_value, columns))

    if max_depth > 0:
        for name, relation in mapper.relationships.items():
            if name in back_relationships:
                continue

            if relation.backref:
                back_relationships.add(name)

            relationship_children = getattr(obj, name)
            if relationship_children is not None:
                if relation.uselist:
                    children = []
                    for child in (
                        c
                        for c in relationship_children
                        if c not in visited_children
                    ):
                        visited_children.add(child)
                        children.append(model_to_dict(
                            child,
                            max_depth=max_depth-1,
                            visited_children=visited_children,
                            back_relationships=back_relationships
                        ))
                    data[name] = children
                else:
                    data[name] = model_to_dict(
                        relationship_children,
                        max_depth=max_depth-1,
                        visited_children=visited_children,
                        back_relationships=back_relationships
                    )

    return data

  ###############################################################################
