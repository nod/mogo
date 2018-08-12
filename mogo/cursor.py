"""
Really, really basic around pymongo.Cursor. Just makes sure
that a result dict is wrapped in a Model to keep everything
clean.
"""

from pymongo.collection import Collection
from pymongo.cursor import Cursor as PyCursor
from pymongo import ASCENDING, DESCENDING

# Shortcuts are better! :)
ASC = ASCENDING
DESC = DESCENDING


class Cursor:
    """ A simple proxy to pymongo's Cursor class. """

    def __init__(self, model, spec=None, *args, **kwargs):
        from .model import Model
        self._order_entries = []
        self._query = spec
        self._model = model
        # there are times we're called with a model, other times it's from
        # within the pymongo lib and we get called with a collection instead of
        # a model
        self._pycur = PyCursor(model._get_collection(), spec, *args, **kwargs)

    def __iter__(self):
        return self

    def __next__(self):
        value = self._pycur.next()
        return self._model(**value)

    def next(self):
        # still need this, since pymongo's cursor still implements next()
        # and returns the raw dict.
        return self.__next__()

    # convenient because if it quacks like a list...
    def __len__(self):
        return self._pycur.count()

    def count(self):
        return self._pycur.count()

    def __getitem__(self, *args, **kwargs):
        value = self._pycur.__getitem__(*args, **kwargs)
        if type(value) == self.__class__:
            return value
        return self._model(**value)

    def first(self):
        if self.__len__() == 0:
            return None
        return self[0]

    def order(self, **kwargs):
        if len(kwargs) < 1:
            raise ValueError("order() requires one field = ASC or DESC.")
        for key, value in kwargs.items():
            if value not in (ASC, DESC):
                raise TypeError("Order value must be mogo.ASC or mogo.DESC.")
            self._order_entries.append((key, value))
            # According to the docs, only the LAST .sort() matters to
            # pymongo, so this SHOULD be safe
            self._pycur.sort(self._order_entries)
        return self

    def limit(self, *args, **kwargs):
        self._pycur.limit(*args, **kwargs)

    def skip(self, *args, **kwargs):
        self._pycur.skip(*args, **kwargs)

    def sort(self, key, direction=ASC):
        return self.order(**{key:direction})

    def rawsort(self, sort_args):
        self._pycur.sort(sort_args)
        return self

    def update(self, modifier):
        if self._query is None:
            raise ValueError(
                "Cannot update on a cursor without a query. If you "
                "actually want to modify all values on a model, pass "
                "in an explicit {} to find().")
        self._model.update(self._query, modifier, multi=True)
        return self

    def change(self, **kwargs):
        modifier = {"$set": kwargs}
        return self.update(modifier)
