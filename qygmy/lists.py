
import pickle

import mpd
from PySide.QtCore import *

from .connection import *


class SongList(RelayingConnection, QAbstractTableModel):

    def __init__(self, parent, current, state_class=State):
        super().__init__(parent)
        self.setSupportedDragActions(Qt.MoveAction | Qt.CopyAction)
        self.songs = []
        # TODO:
        prefix = self.__class__.__name__.lower() + '_'

        state_class.create(self, 'current', current, not_callable, prefix)
        State.create(self, 'current_pos', -1, 'play', prefix)
        self.current.changed.connect(self._update)
        self.current_pos.changed2.connect(self._update_current_pos)
        self.state.changed2.connect(self._reset)

        self.total_length = 0

    def retrieve_from_server(self, newcurrent):
        return []

    def sort_key(self, item):
        return (item.get('file', ''), item.get('directory', ''), item.get('playlist', ''))

    def refresh(self):
        self.current.update(self.current.value, force=True)

    def refresh_format(self):
        self.beginResetModel()
        self.endResetModel()

    def _reset(self, newstate, oldstate):
        if newstate == 'disconnect' or oldstate == 'disconnect':
            self.current.update(None, force=True)

    @mpd_cmd_ignore_conn
    def _update(self, newcurrent):
        self.total_length = 0
        self.beginResetModel()
        try:
            if self.state.value != 'disconnect':
                s = self.retrieve_from_server(newcurrent)
                s.sort(key=self.sort_key)
                self.songs = s
            else:
                self.songs = []
        except (mpd.MPDError, OSError):
            self.songs = []
            raise
        finally:
            self.endResetModel()
        for s in self.songs:
            if 'time' in s:
                self.total_length += int(s['time'])

    def _update_current_pos(self, new, old):
        for i in (old, new):
            if 0 <= i < len(self):
                index1 = self.index(i, 0)
                index2 = self.index(i, self.columnCount() - 1)
                self.dataChanged.emit(index1, index2)

    def __len__(self):
        return len(self.songs)

    def __getitem__(self, index):
        if type(index) == slice or 0 <= index < len(self):
            return self.songs[index]
        return {}

    def __iter__(self):
        return iter(self.songs)

    def details(self, positions):
        if len(positions) == 1 and 'file' in self[positions[0]]:
            return self[positions[0]]

    def can_add_to_current(self, positions):
        return False

    def can_remove(self, positions):
        return False

    def can_rename(self, positions):
        return False

    def can_set_priority(self, positions, prio):
        return False

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
            elif role == Qt.BackgroundRole and self[r].get('prio', '0') != '0':
                return self.main.fmt.high_prio_background
        return None

    def flags(self, index):
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsDragEnabled
        if index.column() == 0 and self.can_rename([index.row()]):
            f |= Qt.ItemIsEditable
        return f

    def supportedDropActions(self):
        return None

    MIMETYPE = 'application/x-qygmy-playlistitems'

    def mimeTypes(self):
        return [self.MIMETYPE]

    def mimeData(self, indexes):
        data = {'source': self.__class__.__name__, 'items': []}
        for i in indexes:
            if i.column() == 0:
                d = {'pos': i.row()}
                for k in ('id', 'playlist', 'directory', 'file'):
                    if k in self[i.row()]:
                        d[k] = self[i.row()][k]
                data['items'].append(d)
        data['items'].sort(key=lambda x: x['pos'])
        md = QMimeData()
        if len(data['items']) > 0:
            # TODO: PickleError
            md.setData(self.MIMETYPE, pickle.dumps(data))
        return md


class WritableMixin:

    def can_remove(self, positions):
        return len(positions) > 0

    @mpd_cmdlist
    def _remove(self, positions):
        for pos in reversed(sorted(positions)):
            if self[pos]:
                song = self[pos].copy()
                song['pos'] = pos
                self.remove_one(song)

    def remove(self, positions):
        if self.can_remove(positions):
            self._remove(positions)
            self.refresh()

    def flags(self, index):
        return super().flags(index) | Qt.ItemIsDropEnabled

    def supportedDropActions(self):
        return Qt.MoveAction | Qt.CopyAction

    def dropMimeData(self, data, action, row, column, parent):
        # Ignoring action: move when src list is same as dst list,
        # copy otherwise.
        if not data.hasFormat(self.MIMETYPE):
            return False
        if row < 0:
            row = parent.row()
        if row < 0:
            row = None
        d = pickle.loads(data.data(self.MIMETYPE).data())
        if d['source'] == self.__class__.__name__:
            if row is None:
                return False
            self._move(d['items'], row)
        else:
            self.add(d['items'], pos=row)
        self.refresh()
        return False

    @mpd_cmdlist
    def _move(self, song_list, pos):
        for s in song_list:
            if s['pos'] >= pos:
                pos += 1
            self.move_one(s, pos)


class Queue(WritableMixin, SongList):

    def __init__(self, parent):
        super().__init__(parent, -1)

    def sort_key(self, item):
        return 0 # no sorting

    def retrieve_from_server(self, new_version):
        return self.conn.playlistinfo()

    def refresh(self):
        self.refresh_format()

    @mpd_cmdlist
    def add(self, song_list, play=False, replace=False, pos=None):
        if replace:
            self.conn.clear()
        cnt = len(song_list)
        for s in song_list:
            if 'playlist' in s:
                self.conn.load(s['playlist'])
            elif 'directory' in s:
                self.conn.add(s['directory'])
            elif 'file' in s:
                if pos is not None:
                    pos += 1
                    self.conn.addid(s['file'], pos)
                else:
                    self.conn.add(s['file'])
            else:
                cnt -= 1
        if play and cnt > 0:
            self.conn.play(0 if replace else len(self))

    def remove_one(self, song):
        self.conn.deleteid(song['id'])

    def move_one(self, song, pos):
        self.conn.moveid(song['id'], pos)

    def can_set_priority(self, positions, prio):
        return any((self[i].get('prio', '0') == '0') != (int(prio) == 0) for i in positions)

    @mpd_cmd
    def set_priority(self, positions, prio):
        self.conn.prioid(prio, *[self[i]['id'] for i in positions])

    def double_clicked(self, pos):
        self.current_pos.send(pos)


class BrowserList(SongList):

    def can_add_to_queue(self, positions):
        return len(positions) > 0

    def add_to_queue(self, positions, play=False, replace=False):
        if self.can_add_to_queue(positions):
            self.parent.queue.add([self[i] for i in positions], play, replace)

    def add_or_cd(self, pos):
        self.add_to_queue([pos])

    def cd(self, newcurrent):
        self.current.update(newcurrent, force=True)

    def double_clicked(self, pos):
        self.add_or_cd(pos)


class Database(BrowserList):

    def __init__(self, parent):
        super().__init__(parent, '', PathState)

    def retrieve_from_server(self, new_path):
        ls = self.conn.lsinfo(new_path)
        return [e for e in ls if 'file' in e or 'directory' in e]

    def add_or_cd(self, pos):
        if 'directory' in self[pos]:
            self.cd(self[pos]['directory'])
        else:
            super().add_or_cd(pos)


class Playlists(WritableMixin, BrowserList):

    def __init__(self, parent):
        super().__init__(parent, '')

    def retrieve_from_server(self, new_name):
        if new_name == '':
            return self.conn.listplaylists()
        else:
            return self.conn.listplaylistinfo(new_name)

    def sort_key(self, item):
        # no sorting inside playlist
        return item['playlist'] if 'playlist' in item else 0

    @mpd_cmdlist
    def add(self, song_list, pos=None):
        # TODO: use 'song' or 'item' consistently
        if self.current.value != '':
            name = self.current.value
        elif pos is not None:
            name = self[pos]['playlist']
        else:
            playlists = {s['playlist'] for s in self}
            name = new = self.tr('new_playlist')
            if name in playlists:
                for i in range(2, 10000):
                    name = '{}_{}'.format(new, i)
                    if name not in playlists:
                        break
        for s in song_list:
            # TODO: directories?
            if 'file' in s:
                self.conn.playlistadd(name, s['file'])

    def can_rename(self, positions):
        return len(positions) == 1 and 'playlist' in self[positions[0]]

    def add_or_cd(self, pos):
        if 'playlist' in self[pos]:
            self.cd(self[pos]['playlist'])
        else:
            super().add_or_cd(pos)

    def remove_one(self, song):
        if self.current.value == '':
            self.conn.rm(song['playlist'])
        else:
            self.conn.playlistdelete(self.current.value, song['pos'])

    def move_one(self, song, pos):
        if self.current.value != '':
            self.conn.playlistmove(self.current.value, song['pos'], pos)

    @mpd_cmd
    def save_current(self, name, replace=False):
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

    @mpd_cmd
    def setData(self, index, value, role=Qt.EditRole):
        r, c = index.row(), index.column()
        if role == Qt.EditRole and c == 0:
            name, new_name = self[r].get('playlist'), str(value)
            if name and name != new_name:
                self.conn.rename(name, new_name)
                self.refresh()
        return False


class Search(BrowserList):

    search_tags = [
        'any',
        'title',
        'artist',
        'album',
        'comment',
        'file',
    ]

    def __init__(self, parent):
        super().__init__(parent, (0, ''))

    def retrieve_from_server(self, new_query):
        if new_query[1] == '':
            return []
        return self.conn.search(self.search_tags[new_query[0]], new_query[1])

