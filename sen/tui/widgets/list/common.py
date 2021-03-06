import logging
import threading

import urwid

from sen.tui.widgets.list.base import VimMovementListBox
from sen.util import _ensure_unicode


logger = logging.getLogger(__name__)


class ScrollableListBox(VimMovementListBox):
    def __init__(self, text):
        text = _ensure_unicode(text)
        list_of_texts = text.split("\n")
        self.walker = urwid.SimpleFocusListWalker([
            urwid.AttrMap(urwid.Text(t, align="left", wrap="any"), "main_list_dg", "main_list_white")
            for t in list_of_texts
        ])
        super().__init__(self.walker)


class AsyncScrollableListBox(VimMovementListBox):
    def __init__(self, generator, ui, static_data=None):
        self.log_texts = []
        if static_data:
            static_data = _ensure_unicode(static_data).split("\n")
            for d in static_data:
                log_entry = d.strip()
                if log_entry:
                    self.log_texts.append(urwid.Text(("main_list_dg", log_entry),
                                                     align="left", wrap="any"))
        walker = urwid.SimpleFocusListWalker(self.log_texts)
        super(AsyncScrollableListBox, self).__init__(walker)

        def fetch_logs():
            for line in generator:
                line = _ensure_unicode(line)
                if self.stop.is_set():
                    break
                if self.filter_query:
                    if self.filter_query not in line:
                        continue
                walker.append(
                    urwid.AttrMap(
                        urwid.Text(line.strip(), align="left", wrap="any"), "main_list_dg", "main_list_white"
                    )
                )
                walker.set_focus(len(walker) - 1)
                ui.refresh()

        self.stop = threading.Event()
        self.thread = threading.Thread(target=fetch_logs, daemon=True)
        self.thread.start()

    def destroy(self):
        self.stop.set()

