
import functools

from PySide.QtCore import *
from mpd import MPDClient, MPDError


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
            return self.default
        if not isinstance(value, type(self.default)):
            return type(self.default)(value)
        return value

    def prepare(self, value):
        return self.normalize(value)

    @classmethod
    def create(cls, parent, name, init, send_callable=None):
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
        s.setObjectName(name)
        s.setParent(parent)
        setattr(parent, name, s)


class BoolState(State):
    def normalize(self, value):
        return value in (True, 1, '1')

    def prepare(self, value):
        return int(self.normalize(value))

    @classmethod
    def create(cls, parent, name, init=False, send_callable=None):
        super().create(parent, name, init, send_callable)


class TimeTupleState(State):
    def normalize(self, value):
        if isinstance(value, (tuple, list)) and len(value) == 2:
            v = tuple(0 if i in ('', None) else int(i) for i in value)
            if v == (0, 0):
                v = (0, 1)
            return v
        return self.default

    def prepare(self, value):
        return int(value)

    @classmethod
    def create(cls, parent, name, init=(0, 1), send_callable=None):
        super().create(parent, name, init, send_callable)


class PathState(State):
    def normalize(self, value):
        v = super().normalize(value)
        return v.strip('/')


def mpd_wrapper(player, function, args=(), kwargs={}):
    r = None
    if player.state.value != 'disconnect':
        try:
            r = function(*args, **kwargs)
        except MPDError as e:
            import sys
            print('{}: {}'.format(type(e).__name__, e), file=sys.stderr)
    player.update()
    return r


def mpd(f):
    @functools.wraps(f)
    def decor(self, *args, **kwargs):
        return mpd_wrapper(self, f, (self,) + args, kwargs)
    return decor


def mpd_cmdlist(f):
    @mpd
    @functools.wraps(f)
    def decor(self, *args, **kwargs):
        self.conn.command_list_ok_begin()
        try:
            return f(self, *args, **kwargs)
        finally:
            self.conn.command_list_end()
    return decor


def simple_mpd(name, *args):
    @Slot()
    @mpd
    def decor(self):
        getattr(self.conn, name)(*args)
    decor.__name__ = name
    return decor


def not_callable(*args):
    raise TypeError("Not Callable")


class Server(QObject):

    search_tags = [
        'any',
        'title',
        'artist',
        'album',
        'comment',
        'file',
    ]

    def __init__(self, formatter, object_name='player'):
        super().__init__()
        self.setObjectName(object_name)

        State.create(self, 'state', 'disconnect', not_callable)
        State.create(self, 'volume', 50, 'setvol')
        State.create(self, 'current_song', {}, not_callable)
        State.create(self, 'current_pos', -1, 'play')
        State.create(self, 'playlist_version', -1, not_callable)
        BoolState.create(self, 'repeat')
        BoolState.create(self, 'shuffle', False, 'random')
        BoolState.create(self, 'single')
        BoolState.create(self, 'consume')
        BoolState.create(self, 'updating_db', False, not_callable)
        TimeTupleState.create(self, 'times', (0, 1), self.seek)

        self.conn = None
        self.state.changed2.connect(self.state_change)

        self.playlist = SonglistModel(formatter)
        self.current_pos.changed.connect(self.playlist.update_current_pos)
        self.playlist_version.changed.connect(self.update_playlist)

        PathState.create(self, 'database_cwd', '', not_callable)
        self.database = SonglistModel(formatter)
        self.database_cwd.changed.connect(self.update_database)

        State.create(self, 'stored_playlists_cwd', '', not_callable)
        self.stored_playlists = SonglistModel(formatter)
        self.stored_playlists_cwd.changed.connect(self.update_stored_playlists)

        State.create(self, 'search_query', (0, ''), not_callable)
        self.search_results = SonglistModel(formatter)
        self.search_query.changed.connect(self.update_search)

    def connect_mpd(self, host, port, password=None):
        if self.conn is not None:
            self.disconnect_mpd()
        self.conn = MPDClient()
        self.conn.connect(host, int(port))
        if password is not None:
            self.conn.password(password)
        self.update()

    @Slot()
    def disconnect_mpd(self):
        if self.conn is not None:
            try:
                self.conn.close()
                self.conn.disconnect()
            finally:
                self.conn = None
        self.update()

    @Slot(str, str)
    def state_change(self, new_state, old_state):
        if new_state == 'disconnect' or old_state == 'disconnect':
            self.database_cwd.update(None, force=True)
            self.stored_playlists_cwd.update(None, force=True)
            self.search_query.update(None, force=True)

    @Slot()
    def update(self):
        if self.conn:
            self.conn.command_list_ok_begin()
            self.conn.status()
            self.conn.currentsong()
            s, c = self.conn.command_list_end()
        else:
            s, c = {'state': 'disconnect'}, {}

        self.state.update(s['state'])
        self.times.update(s.get('time', ':').split(':'))
        self.volume.update(s.get('volume'))
        self.repeat.update(s.get('repeat'))
        self.shuffle.update(s.get('random'))
        self.current_song.update(c)
        self.current_pos.update(s.get('song'))
        self.playlist_version.update(s.get('playlist'))
        self.single.update(s.get('single'))
        self.consume.update(s.get('consume'))
        self.updating_db.update('updating_db' in s)

    @Slot(int)
    def update_playlist(self, new_version):
        if new_version != -1:
            self.playlist.update_list(mpd_wrapper(self, self.conn.playlistinfo))
        else:
            self.playlist.update_list([])

    @Slot(str)
    def update_database(self, path):
        if self.state.value == 'disconnect':
            self.database.update_list([])
        else:
            ls = mpd_wrapper(self, self.conn.lsinfo, [path])
            ls = [e for e in ls if 'file' in e or 'directory' in e]
            ls.sort(key=lambda x: (x.get('file', ''), x.get('directory', '')))
            self.database.update_list(ls)

    @Slot(str)
    def update_stored_playlists(self, name):
        if self.state.value == 'disconnect':
            self.stored_playlists.update_list([])
        elif name == '':
            ls = mpd_wrapper(self, self.conn.listplaylists)
            ls.sort(key=lambda x: x.get('playlist', ''))
            self.stored_playlists.update_list(ls)
        else:
            ls = mpd_wrapper(self, self.conn.listplaylistinfo, [name])
            ls.sort(key=lambda x: x.get('file', ''))
            self.stored_playlists.update_list(ls)

    @Slot(tuple)
    def update_search(self, query):
        if self.state.value == 'disconnect' or query[1] == '':
            self.search_results.update_list([])
        else:
            ls = mpd_wrapper(self, self.conn.search, [self.search_tags[query[0]], query[1]])
            ls.sort(key=lambda x: x.get('file', ''))
            self.search_results.update_list(ls)

    def seek(self, conn, time):
        if self.state.value != 'stop':
            conn.seek(self.current_pos.value, time)

    @mpd
    def updatedb(self):
        if not self.updating_db.value:
            self.conn.update()

    play = simple_mpd('play')
    pause = simple_mpd('pause', 1)
    stop = simple_mpd('stop')
    previous = simple_mpd('previous')
    next = simple_mpd('next')
    clear = simple_mpd('clear')

    @mpd_cmdlist
    def remove(self, positions):
        for i in positions:
            self.conn.deleteid(self.playlist.songs[i]['id'])

    @mpd_cmdlist
    def add(self, data_list, play=False):
        for d in data_list:
            if 'playlist' in d:
                self.conn.load(d['playlist'])
            else:
                self.conn.add(d.get('file', d.get('directory')))
        if play:
            self.conn.play(len(self.playlist))

    def database_add_or_cd(self, pos):
        if 0 <= pos < len(self.database):
            data = self.database.songs[pos]
            if 'directory' in data:
                self.database_cwd.update(data['directory'])
            else:
                self.database_add([pos])

    def playlists_add_or_cd(self, pos):
        if 0 <= pos < len(self.stored_playlists):
            data = self.stored_playlists.songs[pos]
            if 'playlist' in data:
                self.stored_playlists_cwd.update(data['playlist'])
            else:
                self.playlists_add([pos])

    def database_add(self, positions, play=False):
        self.add((self.database.songs[i] for i in sorted(positions)), play)

    def playlists_add(self, positions, play=False):
        self.add((self.stored_playlists.songs[i] for i in sorted(positions)), play)

    def search_add(self, positions, play=False):
        self.add((self.search_results.songs[i] for i in sorted(positions)), play)

    @mpd_cmdlist
    def _playlists_remove(self, positions):
        if self.stored_playlists_cwd.value == '':
            names = [self.stored_playlists.songs[i]['playlist'] for i in positions]
            for n in names:
                self.conn.rm(n)
        else:
            for i in reversed(sorted(positions)):
                print('playlistdelete', self.stored_playlists_cwd.value, i)
                self.conn.playlistdelete(self.stored_playlists_cwd.value, i)

    def playlists_remove(self, positions):
        self._playlists_remove(positions)
        self.stored_playlists_cwd.update(self.stored_playlists_cwd.value, force=True)


class SonglistModel(QAbstractTableModel):

    def __init__(self, formatter):
        super().__init__()
        self.songs = []
        self.current = -1
        self.fmt = formatter

    def update_list(self, songs):
        self.beginResetModel()
        self.songs = songs
        self.endResetModel()

    @Slot(int)
    def update_current_pos(self, pos):
        old = self.current
        self.current = pos
        for i in (old, pos):
            if 0 <= i < len(self):
                index1 = self.index(i, 0)
                index2 = self.index(i, self.columnCount() - 1)
                self.dataChanged.emit(index1, index2)

    def __len__(self):
        return len(self.songs)

    def __getitem__(self, index):
        return self.songs[index]

    def columnCount(self, parent=None):
        return self.fmt.playlist_column_count

    def rowCount(self, parent=None):
        return len(self)

    def data(self, index, role=Qt.DisplayRole):
        if 0 <= index.row() < len(self):
            if role == Qt.DisplayRole:
                return self.fmt.playlist_entry(
                        self.songs[index.row()],
                        index.column(),
                        index.row() == self.current)
            elif role == Qt.ToolTipRole:
                return self.fmt.playlist_tooltip(
                        self.songs[index.row()],
                        index.column(),
                        index.row() == self.current)
            elif role == Qt.DecorationRole:
                return self.fmt.playlist_icon(
                        self.songs[index.row()],
                        index.column(),
                        index.row() == self.current)
            #elif role == Qt.EditRole and index.column() == 0:
            #    return self.songs[index.row()].get('playlist', None)
        return None

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable #| Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled

    #def supportedDropActions(self):
    #    return Qt.MoveAction

