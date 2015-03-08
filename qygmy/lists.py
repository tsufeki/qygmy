
import pickle
from abc import ABCMeta, abstractmethod

import mpd
from PySide.QtCore import *

from .connection import *


class QABCMeta(ABCMeta, QObject.__class__):
    """A little hack to allow the use of ABCMeta."""


class SongList(RelayingConnection, QAbstractTableModel, metaclass=QABCMeta):

    current_pos = type('current_pos', (), {'value': -1})()

    def __init__(self, parent, current, state_class=State):
        super().__init__(parent)
        self.setSupportedDragActions(Qt.MoveAction | Qt.CopyAction)
        self.items = []

        state_class.create(self, 'current', current, not_callable)
        self.current.changed.connect(self._update)
        self.state.changed2.connect(self._reset)

        self.total_length = 0

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        if type(index) == slice or 0 <= index < len(self):
            return self.items[index]
        return {}

    def __iter__(self):
        return iter(self.items)

    def refresh_format(self):
        self.beginResetModel()
        self.endResetModel()

    def details(self, positions):
        if len(positions) == 1 and 'file' in self[positions[0]]:
            return self[positions[0]]

    @abstractmethod
    def ls(self, identifier):
        return []

    def can_add_to_queue(self, positions):
        return False

    def can_remove(self, positions):
        return False

    def can_rename(self, positions):
        return False

    def can_set_priority(self, positions, prio):
        return False

    def can_copy(self, positions):
        return False

    def can_add_url(self):
        return False

    @abstractmethod
    def item_chosen(self, pos):
        """i.e. double-clicked or Return pressed."""

    def sorted(self, items):
        items = [(self.main.fmt.sort_order(item), item) for item in items]
        cols = min((len(i[0]) for i in items), default=0)
        for i in range(cols - 1, -1, -1):
            items.sort(key=lambda kitem: kitem[0][i], reverse=i % 2 == 1)
        return [item[1] for item in items]

    def _reset(self, newstate, oldstate):
        if newstate == 'disconnect' or oldstate == 'disconnect':
            self.current.update(None, force=True)

    def _update(self, new_current):
        self.main.busy()
        self.total_length = 0
        self.beginResetModel()
        self.items = []
        if self.state.value != 'disconnect':
            self.items = self.ls(new_current)
        self.endResetModel()
        for i in self.items:
            if 'time' in i:
                self.total_length += int(i['time'])
        self.main.not_busy()

    def columnCount(self, parent=None):
        return self.main.fmt.playlist_column_count

    def rowCount(self, parent=None):
        return len(self)

    def data(self, index, role=Qt.DisplayRole):
        r, c = index.row(), index.column()
        if 0 <= r < len(self):
            if role == Qt.DisplayRole:
                return self.main.fmt.playlist_item(
                        self[r], c, r == self.current_pos.value)
            elif role == Qt.ToolTipRole:
                return self.main.fmt.playlist_tooltip(
                        self[r], c, r == self.current_pos.value)
            elif role == Qt.DecorationRole:
                return self.main.fmt.playlist_icon(
                        self[r], c, r == self.current_pos.value)
            elif role == Qt.BackgroundRole:
                return self.main.fmt.playlist_background(
                        self[r], c, r == self.current_pos.value)
        return None

    def flags(self, index):
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
        if index.column() == 0 and self.can_rename([index.row()]):
            f |= Qt.ItemIsEditable
        return f

    def mimeData(self, indexes):
        data = {'source': id(self), 'items': []}
        for i in indexes:
            if i.column() == 0:
                d = {'pos': str(i.row())}
                for k in ('id', 'playlist', 'directory', 'file'):
                    if k in self[i.row()]:
                        d[k] = self[i.row()][k]
                data['items'].append(d)
        data['items'].sort(key=lambda x: int(x['pos']))
        md = QMimeData()
        if len(data['items']) > 0:
            md.setData(self.MIMETYPE, pickle.dumps(data))
        return md

    def mimeTypes(self):
        return [self.MIMETYPE]

    def supportedDropActions(self):
        return None

    MIMETYPE = 'application/x-qygmy-playlistitems'


class WritableMixin(metaclass=ABCMeta):

    @mpd_cmd(fallback=False)
    def add(self, items, pos=None, **kwargs):
        a = []
        for i in items:
            if 'file' in i or self.can_add_directly(i, pos, **kwargs):
                a.append(i)
            elif 'directory' in i:
                a.extend(self.parent.database.ls(i['directory'], recursive=True))
            elif 'playlist' in i:
                a.extend(self.parent.playlists.ls(i['playlist']))
        if len(a) == 0:
            return False
        if pos is not None:
            a = reversed(a)
        last = len(self)
        with self.mpd_cmdlist():
            for i in a:
                self.add_one(i, pos, last, **kwargs)
                last += 1
        return True

    @abstractmethod
    def can_add_directly(self, item, pos, **kwargs):
        return True

    @abstractmethod
    def add_one(self, item, pos, last, **kwargs):
        pass

    def can_add_url(self):
        return True

    def add_url(self, url):
        self.add([{'file': url}])

    def can_remove(self, positions):
        return len(positions) > 0

    @mpd_cmd
    def remove(self, positions):
        if self.can_remove(positions):
            items = []
            for pos in positions:
                i = self[pos].copy()
                i['pos'] = str(pos)
                items.append(i)
            with self.mpd_cmdlist():
                for i in reversed(sorted(items, key=lambda x: int(x['pos']))):
                    self.remove_one(i)

    @abstractmethod
    def remove_one(self, item):
        pass

    def can_copy(self, positions):
        return len(positions) > 0

    def copy(self, positions):
        if self.can_copy(positions):
            self.add([self[i] for i in positions], max(positions) + 1)

    @mpd_cmd
    def move(self, items, pos):
        if len(items) == 0:
            return
        items.sort(key=lambda x: int(x['pos']))
        a = [i for i in items if int(i['pos']) <= pos]
        b = (i for i in items if int(i['pos']) > pos)
        apos = pos
        bpos = pos + (0 if len(a) == 0 else 1)
        with self.mpd_cmdlist():
            for i in reversed(a):
                if apos != i['pos']:
                    self.move_one(i, apos)
                apos -= 1
            for i in b:
                if bpos != i['pos']:
                    self.move_one(i, bpos)
                bpos += 1

    @abstractmethod
    def move_one(self, item, pos):
        pass

    def dropMimeData(self, data, action, row, column, parent):
        # Ignoring the action argument: move when src list is same as dst list,
        # copy otherwise.
        if not data.hasFormat(self.MIMETYPE):
            return False
        if row < 0:
            row = parent.row()
        if row < 0:
            row = None
        d = pickle.loads(data.data(self.MIMETYPE).data())
        if d['source'] == id(self):
            if row is None:
                row = len(self) - 1
            self.move(d['items'], row)
        else:
            self.add(d['items'], row)
        return False

    def flags(self, index):
        return super().flags(index) | Qt.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.MoveAction | Qt.CopyAction


class Queue(WritableMixin, SongList):

    def __init__(self, parent):
        super().__init__(parent, -1)
        State.create(self, 'current_pos', -1, 'play')
        self.current_pos.changed2.connect(self._update_current_pos)

    def refresh(self):
        super().refresh()
        self.refresh_format()

    @mpd_cmd(fallback=[], refresh=False)
    def ls(self, _=None):
        return self.conn.playlistinfo()

    @mpd_cmd(fallback=False, refresh=False)
    def add(self, items, pos=None, play=False, replace=False, priority=0):
        if replace:
            self.conn.clear()
        r = super().add(items, pos, priority=priority)
        if play and r:
            if replace:
                playpos = 0
            else:
                playpos = len(self) - 1 if pos is None else pos
            self.conn.play(playpos)
        return r

    def can_add_directly(self, item, pos, priority):
        return 'file' in item or ('playlist' in item and pos is None and priority == 0)

    def add_one(self, item, pos, last, priority):
        if 'playlist' in item and pos is None and priority == 0:
            self.conn.load(item['playlist'])
        elif 'file' in item:
            if pos is None:
                pos = last
                self.conn.add(item['file'])
            else:
                self.conn.addid(item['file'], pos)
            if priority != 0:
                self.conn.prio(priority, pos)

    def remove_one(self, item):
        self.conn.deleteid(item['id'])

    def move_one(self, item, pos):
        self.conn.moveid(item['id'], pos)

    def can_set_priority(self, positions, prio):
        return any((self[i].get('prio', '0') == '0') != (int(prio) == 0) for i in positions)

    @mpd_cmd
    def set_priority(self, positions, prio):
        if self.can_set_priority(positions, prio):
            ids = [self[i]['id'] for i in positions]
            batch_size = self.MAX_MPD_ARGUMENTS - 1
            with self.mpd_cmdlist():
                for k in range((len(ids) - 1) // batch_size + 1):
                    b = ids[k * batch_size:(k+1) * batch_size]
                    self.conn.prioid(prio, *b)

    @mpd_cmd
    def reverse(self):
        with self.mpd_cmdlist():
            n = len(self)
            for i in range(n//2 + 1):
                self.conn.swap(i, n-i-1)

    def item_chosen(self, pos):
        self.current_pos.send(pos)

    def _update_current_pos(self, new, old):
        for i in (old, new):
            if 0 <= i < len(self):
                index1 = self.index(i, 0)
                index2 = self.index(i, self.columnCount() - 1)
                self.dataChanged.emit(index1, index2)


class BrowserList(SongList):

    def __init__(self, parent, current, state_class=State):
        super().__init__(parent, current, state_class)
        self.parent.updating_db.changed2.connect(self._updating_db_changed)

    def _updating_db_changed(self, new, old):
        if old and not new:
            self.refresh()

    def refresh(self):
        super().refresh()
        self.current.update(self.current.value, force=True)

    def can_add_to_queue(self, positions):
        return len(positions) > 0

    def add_to_queue(self, positions, play=False, replace=False, priority=0):
        if self.can_add_to_queue(positions):
            self.parent.queue.add([self[i] for i in sorted(positions)],
                    play=play, replace=replace, priority=priority)

    def item_chosen(self, pos):
        self.add_to_queue([pos])

    def cd(self, new_current):
        self.current.update(new_current, force=True)


class Database(BrowserList):

    def __init__(self, parent):
        super().__init__(parent, '', PathState)

    def item_chosen(self, pos):
        if 'directory' in self[pos]:
            self.cd(self[pos]['directory'])
        else:
            super().item_chosen(pos)

    @mpd_cmd(fallback=[], refresh=False)
    def ls(self, path, recursive=False):
        l = self.conn.lsinfo(path)
        r = []
        for e in self.sorted(l):
            if 'file' in e or (not recursive and 'directory' in e):
                r.append(e)
            elif 'directory' in e:
                r.extend(self.ls(e['directory'], recursive=True))
        return r


class Playlists(WritableMixin, BrowserList):

    def __init__(self, parent):
        super().__init__(parent, '')
        self.NEW_PLAYLIST_NAME = self.tr('New playlist')

    @mpd_cmd(fallback=[], refresh=False)
    def ls(self, name):
        if name != '':
            return self.conn.listplaylistinfo(name)
        return self.sorted(self.conn.listplaylists())

    def add(self, items, pos=None):
        if self.current.value != '':
            name = self.current.value
        elif pos is not None:
            name = self[pos]['playlist']
            pos = None
        else:
            playlists = {s['playlist'] for s in self}
            name = new = self.NEW_PLAYLIST_NAME
            if name in playlists:
                for i in range(2, 10000):
                    name = '{}_{}'.format(new, i)
                    if name not in playlists:
                        break
            pos = None
        return super().add(items, pos, name=name)

    def can_add_directly(self, item, pos, name):
        return 'file' in item

    def add_one(self, item, pos, last, name):
        if 'file' not in item:
            return
        if pos is not None:
            self.conn.playlistadd(name, item['file'])
            self.conn.playlistmove(name, last, pos)
        else:
            self.conn.playlistadd(name, item['file'])

    def can_rename(self, positions):
        return len(positions) == 1 and 'playlist' in self[positions[0]]

    def item_chosen(self, pos):
        if 'playlist' in self[pos]:
            self.cd(self[pos]['playlist'])
        else:
            super().item_chosen(pos)

    def remove_one(self, item):
        if 'playlist' in item:
            self.conn.rm(item['playlist'])
        else:
            self.conn.playlistdelete(self.current.value, item['pos'])

    def can_copy(self, positions):
        return False if self.current.value == '' else super().can_copy(positions)

    def move_one(self, item, pos):
        if self.current.value != '':
            self.conn.playlistmove(self.current.value, item['pos'], pos)

    @mpd_cmd(refresh=False)
    def save_queue(self, name, replace=False):
        try:
            self.conn.save(name)
        except mpd.CommandError as e:
            if self.parse_exception(e)[0] != '56':
                raise
            if not replace:
                return False
            self.conn.rm(name)
            self.conn.save(name)
        if self.current.value in ('', name):
            self.refresh()
        return True

    def data(self, index, role=Qt.DisplayRole):
        r, c = index.row(), index.column()
        if role == Qt.EditRole and c == 0:
            return self[r].get('playlist', None)
        else:
            return super().data(index, role)

    @mpd_cmd(fallback=False, refresh=False)
    def setData(self, index, value, role=Qt.EditRole):
        r, c = index.row(), index.column()
        if role == Qt.EditRole and c == 0:
            name, new_name = self[r].get('playlist'), str(value)
            if name and name != new_name:
                self.conn.rename(name, new_name)
                self.refresh()
        return False


class SearchTags(RelayingConnection, QAbstractListModel):

    def __init__(self, parent):
        super().__init__(parent)
        self.tags = []
        self.retranslate()
        self.state.changed2.connect(self._update)

    def retranslate(self):
        self.standard_tags = [
            ('title', self.tr('Title')),
            ('artist', self.tr('Artist')),
            ('album', self.tr('Album')),
            ('genre', self.tr('Genre')),
            ('comment', self.tr('Comment')),
            ('composer', self.tr('Composer')),
            ('performer', self.tr('Performer')),
            ('date', self.tr('Date')),
            ('track', self.tr('Track')),
            ('disc', self.tr('Disc')),
            ('name', self.tr('Name')),
        ]
        self.special_tags = [
            ('any', self.tr('Any')),
            ('file', self.tr('File name')),
        ]

    def refresh(self):
        super().refresh()
        self.beginResetModel()
        self.tags = []
        tags = set(self._tag_types())
        for t in self.special_tags:
            tags.discard(t[0])
        self.tags.append(self.special_tags[0])
        for t in self.standard_tags:
            if t[0] in tags:
                self.tags.append(t)
                tags.discard(t[0])
        self.tags.append(self.special_tags[1])
        for t in sorted(tags):
            if not t.startswith('musicbrainz_'):
                self.tags.append((t, t))
        self.endResetModel()

    @mpd_cmd(fallback=[], refresh=False)
    def _tag_types(self):
        return (t.lower() for t in self.conn.tagtypes())

    def _update(self, newstate, oldstate):
        if newstate != 'disconnect' and oldstate == 'disconnect':
            self.refresh()

    def rowCount(self, parent=None):
        return len(self.tags)

    def data(self, index, role=Qt.DisplayRole):
        i = index.row()
        if 0 <= i < self.rowCount():
            if role == Qt.DisplayRole:
                return self.tags[i][1]
            elif role == Qt.UserRole:
                return self.tags[i][0]


class Search(BrowserList):

    def __init__(self, parent):
        super().__init__(parent, ('', ''))
        self.search_tags = SearchTags(self)

    @mpd_cmd(fallback=[], refresh=False)
    def ls(self, query):
        if query[0] in ('', None) or query[1] in ('', None):
            return []
        return self.sorted(self.conn.search(query[0], query[1]))

