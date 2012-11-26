"""Pagination

This code based on the django.core.paginator module of the Django Project.
"""
from math import ceil

from weblib.document import Document


class Paginator(object):
    def __init__(self, object_list, per_page, orphans=0,
                 allow_empty_first_page=True):
        self.object_list = object_list
        self.per_page = int(per_page)
        self.orphans = int(orphans)
        self.allow_empty_first_page = allow_empty_first_page
        if len(self.object_list) == 0:
            if self.allow_empty_first_page:
                self.len = 1
            else:
                self.len = 0
        else:
            hits = max(1, len(self.object_list) - self.orphans)
            self.len = int(ceil(hits / float(self.per_page)))

    def __len__(self):
        return self.len

    def __getitem__(self, key):
        if isinstance(key, slice):
            return list(self.__getitem__(i) for i in key.indices(self.len))
        elif not isinstance(key, int):
            raise TypeError("index must be an integer or a slice")
        if key < 0:
            key += self.len
        if key >= self.len or key < 0:
            raise IndexError("page index out of range")
        bottom = key * self.per_page
        top = bottom + self.per_page
        if top + self.orphans >= len(self.object_list):
            top = len(self.object_list)
        return Page(self.object_list[bottom:top], key, self)


class Page(list, Document):
    def __init__(self, object_list, number, paginator):
        super().__init__(object_list)
        self.number = number
        self.paginator = paginator

    def has_next(self):
        return self.number < len(self.paginator) - 1

    def has_previous(self):
        return self.number > 0

    def has_other_pages(self):
        return self.has_previous() or self.has_next()

    def next_page_number(self):
        return self.number + 1

    def previous_page_number(self):
        return self.number - 1

    def start_index(self):
        """
        Returns the 0-based index of the first object on this page,
        relative to total objects in the paginator.
        """
        # Special case, return zero if no items.
        if len(self.paginator.object_list) == 0:
            return 0
        return self.paginator.per_page * self.number

    def end_index(self):
        """
        Returns the 0-based index of the last object on this page,
        relative to total objects found (hits).
        """
        # Special case for the last page because there can be orphans.
        if self.number == len(self.paginator) - 1:
            return len(self.paginator.object_list)
        return self.number * self.paginator.per_page
