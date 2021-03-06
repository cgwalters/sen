import logging

import urwid
from sen.exceptions import NotifyError


logger = logging.getLogger(__name__)


class WidgetBase(urwid.ListBox):
    """
    common class fot widgets
    """

    def __init__(self, *args, **kwargs):
        self.search_string = None
        self.filter_query = None
        super().__init__(*args, **kwargs)
        self.ro_content = self.body[:]  # unfiltered content of a widget

    def set_body(self, widgets):
        self.body[:] = widgets

    def reload_widget(self):
        # this is the easiest way to refresh body
        self.body[:] = self.body

    def _search(self, reverse_search=False):
        if self.search_string is None:
            raise NotifyError("No search pattern specified.")
        if not self.search_string:
            self.search_string = None
            return
        pos = self.focus_position
        original_position = pos
        wrapped = False
        while True:
            if reverse_search:
                obj, pos = self.body.get_prev(pos)
            else:
                obj, pos = self.body.get_next(pos)
            if obj is None:
                # wrap
                wrapped = True
                if reverse_search:
                    obj, pos = self.body[-1], len(self.body)
                else:
                    obj, pos = self.body[0], 0
            if wrapped and (
                        (pos > original_position and not reverse_search) or
                        (pos < original_position and reverse_search)
            ):
                self.search_string = None
                raise NotifyError("Pattern not found: %r." % self.search_string)
            # FIXME: figure out nicer search api
            if hasattr(obj, "matches_search"):
                condition = obj.matches_search(self.search_string)
            else:
                condition = self.search_string in obj.original_widget.text
            if condition:
                self.set_focus(pos)
                self.reload_widget()
                break

    def filter(self, s, widgets_to_filter=None):
        s = s.strip()

        if not s:
            self.filter_query = None
            self.body[:] = self.ro_content
            return

        widgets = []
        for obj in widgets_to_filter or self.ro_content:

            # FIXME: figure out nicer search api
            if hasattr(obj, "matches_search"):
                condition = obj.matches_search(s)
            else:
                condition = s in obj.original_widget.text

            if condition:
                widgets.append(obj)
        if not widgets_to_filter:
            self.filter_query = s
        return widgets

    def find_previous(self, search_pattern=None):
        if search_pattern is not None:
            self.search_string = search_pattern
        self._search(reverse_search=True)

    def find_next(self, search_pattern=None):
        if search_pattern is not None:
            self.search_string = search_pattern
        self._search()

    def status_bar(self):
        columns_list = []

        def add_subwidget(markup, color_attr=None):
            if color_attr is None:
                w = urwid.AttrMap(urwid.Text(markup), "status_text")
            else:
                w = urwid.AttrMap(urwid.Text(markup), color_attr)
            columns_list.append((len(markup), w))

        if self.search_string:
            add_subwidget("Search: ")
            add_subwidget(repr(self.search_string))

        if self.search_string and self.filter_query:
            add_subwidget(", ")

        if self.filter_query:
            add_subwidget("Filter: ")
            add_subwidget(repr(self.filter_query))

        return columns_list


class VimMovementListBox(WidgetBase):
    """
    ListBox with vim-like movement which can be inherited in other widgets
    """

    def __init__(self, *args, **kwargs):
        # we want "gg"!
        self.cached_key = None
        super().__init__(*args, **kwargs)

    def keypress(self, size, key):
        logger.debug("VimListBox keypress %r", key)

        # FIXME: workaround so we allow "gg" only, and not "g*"
        if self.cached_key == "g" and key != "g":
            self.cached_key = None

        if key == "j":
            return super().keypress(size, "down")
        elif key == "k":
            return super().keypress(size, "up")
        elif key == "ctrl d":
            try:
                self.set_focus(self.get_focus()[1] + 10)
            except IndexError:
                self.set_focus(len(self.body) - 1)
            self.reload_widget()
            return
        elif key == "ctrl u":
            try:
                self.set_focus(self.get_focus()[1] - 10)
            except IndexError:
                self.set_focus(0)
            self.reload_widget()
            return
        elif key == "G":
            self.set_focus(len(self.body) - 1)
            self.body[:] = self.body
            return
        elif key == "g":
            if self.cached_key is None:
                self.cached_key = "g"
            elif self.cached_key == "g":
                self.set_focus(0)
                self.reload_widget()
                self.cached_key = None
            return
        key = super().keypress(size, key)
        return key
