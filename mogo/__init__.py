""" This is the mogo syntactic sugar library for MongoDB. """

from mogo.model import Model
from mogo.field import Field, ReferenceField
from mogo.connection import connect

__all__ = ['Model', 'connect', 'Field']
