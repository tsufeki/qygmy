
import mpd
from PySide.QtCore import *

from .connection import *
from .lists import *


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
            except (mpd.MPDError, OSError) as e:
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

