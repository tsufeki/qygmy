
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

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)

    def _seek(self, time):
        if self.state.value != 'stop':
            self.conn.seek(self.queue.current_pos.value, time)

    def start_timer(self, interval=500):
        if self.timer.isActive():
            self.timer.stop()
        self.timer.start(interval)

    @mpd_cmd(fallback=({'state': 'disconnect'}, {}), refresh=False)
    def retrieve_state(self):
        with self.mpd_cmdlist() as cl:
            self.conn.status()
            self.conn.currentsong()
        return cl.retval

    def refresh(self):
        s, c = self.retrieve_state()

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

    @mpd_cmd(ignore_conn=True)
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
            self.conn._reset()
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
            self.updating_db.update(True) # so we don't miss even super-short updates

    @mpd_cmd(fallback={}, refresh=False)
    def statistics(self):
        stats = self.conn.stats()
        stats['mpdversion'] = self.conn.mpd_version
        return stats

    @mpd_cmd(fallback=[], refresh=False)
    def outputs(self):
        return sorted((
            i.get('outputname', i['outputid']),
            int(i['outputid']),
            i['outputenabled'] == '1') for i in self.conn.outputs())

    @mpd_cmd
    def enable_output(self, outputid, enable=True):
        if enable:
            self.conn.enableoutput(outputid)
        else:
            self.conn.disableoutput(outputid)

