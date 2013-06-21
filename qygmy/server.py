
import re
import functools
import socket

from PySide.QtCore import *
from mpd import MPDClient, MPDError, CommandError, ConnectionError


class State(QObject):

    default = None
    changed = None
    send_callable = None

    def __init__(self):
        super().__init__()
        self._value = self.normalize(self.default)

    @property
    def value(self):
        return self._value

    def update(self, new_value, force=False):
        new_value = self.normalize(new_value)
        if self._value != new_value or force:
            old_value = self._value
            self._value = new_value
            self.changed.emit(self._value)
            self.changed2.emit(self._value, old_value)

    def send(self, new_value):
        new_value = self.prepare(new_value)
        self.send_callable(new_value)

    def normalize(self, value):
        if value is None or value == '':
            value = self.default
        if isinstance(value, str):
            value = value.strip()
        if not isinstance(value, type(self.default)):
            value = type(self.default)(value)
        return value

    def prepare(self, value):
        return self.normalize(value)

    @classmethod
    def create(cls, parent, name, init, send_callable=None, prefix=''):
        if not callable(send_callable):
            method = send_callable
            if method is None:
                method = name
            send_callable = lambda c, v: getattr(c, method)(v)
        class C(cls):
            default = init
            changed = Signal(type(init))
            changed2 = Signal(type(init), type(init))
            send = Slot(type(init))(cls.send)
            def send_callable(self, v):
                return mpd_wrapper(parent, send_callable, [parent.conn, v])
        s = C()
        s.setObjectName(prefix + name)
        s.setParent(parent)
        setattr(parent, name, s)


class BoolState(State):
    def normalize(self, value):
        return value in (True, 1, '1')

    def prepare(self, value):
        return int(self.normalize(value))

    @classmethod
    def create(cls, parent, name, init=False, send_callable=None, prefix=''):
        super().create(parent, name, init, send_callable, prefix)


class TimeTupleState(State):
    def normalize(self, value):
        if isinstance(value, (tuple, list)):
            v = [0 if i in ('', None, -1, '-1') else int(i) for i in value]
            v = v[:2]
            v = v + [0]*(2 - len(v))
            return v
        return self.default

    def prepare(self, value):
        return int(value)


class PathState(State):
    def normalize(self, value):
        v = super().normalize(value)
        return v.strip('/')


def mpd_wrapper(connection, function, args=(), kwargs={}, ignore_conn=False):
    r = None
    if ignore_conn or connection.state.value != 'disconnect':
        try:
            r = function(*args, **kwargs)
        except (MPDError, socket.error) as e:
            connection.handle_error(e)
    connection.update_state()
    return r


def mpd_cmd(f):
    @functools.wraps(f)
    def decor(self, *args, **kwargs):
        return mpd_wrapper(self, f, (self,) + args, kwargs)
    return decor

def mpd_cmd_ignore_conn(f):
    @functools.wraps(f)
    def decor(self, *args, **kwargs):
        return mpd_wrapper(self, f, (self,) + args, kwargs, True)
    return decor


def mpd_cmdlist(f):
    @mpd_cmd
    @functools.wraps(f)
    def decor(self, *args, **kwargs):
        self.conn.command_list_ok_begin()
        try:
            return f(self, *args, **kwargs)
        finally:
            self.conn.command_list_end()
    return decor


def simple_mpd(name, *args):
    @mpd_cmd
    def f(self):
        getattr(self.conn, name)(*args)
    f.__name__ = name
    return f


def not_callable(*args):
    raise TypeError("Not Callable")


class Connection:

    ERROR = re.compile(r'^\[([0-9]+)@([0-9]+)\] \{([^}]*)\} (.*)$')

    def parse_exception(self, exc):
        m = self.ERROR.match(exc.args[0])
        if m is None:
            return '', '', '', str(exc)
        return m.groups()

    def handle_error(self, exc):
        import sys
        print('{}: {}'.format(type(exc).__name__, exc), file=sys.stderr)
        msg = None
        if isinstance(exc, CommandError):
            errno, cmdno, cmd, msg = self.parse_exception(exc)
            msg = msg + ' ({};{})'.format(errno, cmd)
        elif isinstance(exc, (ConnectionError, socket.error)):
            msg = str(exc)
        if msg:
            self.main.error(msg[0].upper() + msg[1:])
        # TODO: critical errors


class ProperConnection(Connection):
    def __init__(self, main):
        super().__init__(main)
        self.main = main
        self.conn = MPDClient()
        State.create(self, 'state', 'disconnect', not_callable)

    def update_state(self):
        pass


class RelayingConnection(Connection):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

    @property
    def main(self):
        return self.parent.main

    @property
    def conn(self):
        return self.parent.conn

    @property
    def state(self):
        return self.parent.state

    def update_state(self):
        self.parent.update_state()


class Server(ProperConnection, QObject):

    def __init__(self, main):
        super().__init__(main)

        State.create(self, 'volume', 50, 'setvol')
        State.create(self, 'current_song', {}, not_callable)
        BoolState.create(self, 'repeat')
        BoolState.create(self, 'shuffle', False, 'random')
        BoolState.create(self, 'single')
        BoolState.create(self, 'consume')
        BoolState.create(self, 'updating_db', False, not_callable)
        TimeTupleState.create(self, 'times', (0, 0), self._seek)

        self.queue = Queue(self)
        self.database = Database(self)
        self.playlists = Playlists(self)
        self.search = Search(self)

    #def print(self):
    #    for i in ('state', 'volume', 'current_song', 'repeat', 'shuffle', 'single',
    #            'consume', 'updating_db', 'times'):
    #        print(i, '=', getattr(self, i).value)
    #    for i in ('queue', 'database', 'playlists', 'search'):
    #        print(i + '.current', '=', getattr(self, i).current.value)
    #        print(i + '.current_pos', '=', getattr(self, i).current_pos.value)

    def _seek(self, conn, time):
        if self.state.value != 'stop':
            conn.seek(self.queue.current_pos.value, time)

    def update_state(self):
        s, c = {'state': 'disconnect'}, {}
        if self.state.value != 'disconnect':
            try:
                self.conn.command_list_ok_begin()
                self.conn.status()
                self.conn.currentsong()
                s, c = self.conn.command_list_end()
            except MPDError as e:
                self.handle_error(e)

        self.state.update(s['state'])
        self.times.update(s.get('time', ':').split(':'))
        self.volume.update(s.get('volume'))
        self.repeat.update(s.get('repeat'))
        self.shuffle.update(s.get('random'))
        self.current_song.update(c)
        self.single.update(s.get('single'))
        self.consume.update(s.get('consume'))
        self.updating_db.update('updating_db' in s)

        self.queue.current.update(s.get('playlist'))
        self.queue.current_pos.update(s.get('song'))

    @mpd_cmd_ignore_conn
    def connect_mpd(self, host, port, password=None):
        if self.state.value != 'disconnect':
            self.disconnect_mpd()
        # TODO: ValueError
        self.conn.connect(host, int(port))
        self.state.update('connect')
        if password:
            self.conn.password(password)

    @mpd_cmd
    def disconnect_mpd(self):
        try:
            try:
                self.conn.close()
            finally:
                self.conn.disconnect()
        finally:
            self.state.update('disconnect')

    play = simple_mpd('play')
    pause = simple_mpd('pause', 1)
    stop = simple_mpd('stop')
    previous = simple_mpd('previous')
    next = simple_mpd('next')
    clear = simple_mpd('clear')
    randomize_queue = simple_mpd('shuffle')

    @mpd_cmd
    def updatedb(self):
        if not self.updating_db.value:
            self.conn.update()

    @mpd_cmd
    def statistics(self):
        return self.conn.stats()


class SongList(RelayingConnection, QAbstractTableModel):

    def __init__(self, parent, current, state_class=State):
        super().__init__(parent)
        self.songs = []
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
        except MPDError:
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

    def details(self, positions):
        if len(positions) == 1 and 'file' in self[positions[0]]:
            return self[positions[0]]

    def can_add_to_current(self, positions):
        return False

    def can_remove(self, positions):
        return False

    def can_rename(self, positions):
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
        return None

    def flags(self, index):
        f = Qt.ItemIsEnabled | Qt.ItemIsSelectable #| Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled
        if index.column() == 0 and self.can_rename([index.row()]):
            f |= Qt.ItemIsEditable
        return f

    #def supportedDropActions(self):
    #    return Qt.MoveAction


class RemovableItemsMixin:

    def can_remove(self, positions):
        return len(positions) > 0

    @mpd_cmdlist
    def _remove(self, positions):
        for pos in reversed(sorted(positions)):
            if self[pos]:
                self.remove_one(pos)

    def remove(self, positions):
        if self.can_remove(positions):
            self._remove(positions)
            self.refresh()


class Queue(RemovableItemsMixin, SongList):

    def __init__(self, parent):
        super().__init__(parent, -1)

    def sort_key(self, item):
        return 0 # no sorting

    def retrieve_from_server(self, new_version):
        return self.conn.playlistinfo()

    @mpd_cmdlist
    def add(self, song_list, play=False, replace=False):
        if replace:
            self.conn.clear()
        cnt = len(song_list)
        for s in song_list:
            if 'playlist' in s:
                self.conn.load(s['playlist'])
            elif 'directory' in s:
                self.conn.add(s['directory'])
            elif 'file' in s:
                self.conn.add(s['file'])
            else:
                cnt -= 1
        if play and cnt > 0:
            self.conn.play(0 if replace else len(self))

    def remove_one(self, pos):
        self.conn.deleteid(self[pos]['id'])

    @mpd_cmd
    def save(self, name, replace=False):
        try:
            self.conn.save(name)
        except CommandError as e:
            if self.parse_exception(e)[0] != '56':
                raise
            if not replace:
                return False
            self.conn.rm(name)
            self.conn.save(name)
        if self.current.value in ('', name):
            self.refresh()
        return True

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


class Playlists(RemovableItemsMixin, BrowserList):

    def __init__(self, parent):
        super().__init__(parent, '')

    def retrieve_from_server(self, new_name):
        if new_name == '':
            return self.conn.listplaylists()
        else:
            return self.conn.listplaylistinfo(new_name)

    def can_rename(self, positions):
        return len(positions) == 1 and 'playlist' in self[positions[0]]

    def add_or_cd(self, pos):
        if 'playlist' in self[pos]:
            self.cd(self[pos]['playlist'])
        else:
            super().add_or_cd(pos)

    def remove_one(self, pos):
        if self.current.value == '':
            self.conn.rm(self[pos]['playlist'])
        else:
            self.conn.playlistdelete(self.current.value, pos)

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

