
import re
import functools

import mpd
from PySide.QtCore import *

import logging
logger = logging.getLogger('qygmy')


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
        except (mpd.MPDError, OSError) as e:
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
            r = f(self, *args, **kwargs)
        finally:
            self.conn.command_list_end()
        return r
    return decor


def simple_mpd(name, *args):
    @mpd_cmd
    def f(self):
        return getattr(self.conn, name)(*args)
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
        if isinstance(exc, (mpd.ConnectionError, mpd.ProtocolError, OSError)):
            # Critical errors
            try:
                self.conn.disconnect()
            except Exception as e:
                pass
            # Needed because it isn't called when socket's close()
            # raises an exception (python-mpd2 bug(?)).
            self.conn._reset()
            self.state.update('disconnect')
        logger.error('{}: {}'.format(exc.__class__.__name__, exc))
        msg = None
        if isinstance(exc, mpd.CommandError):
            errno, cmdno, cmd, msg = self.parse_exception(exc)
        elif isinstance(exc, OSError) and exc.errno is not None:
            msg = exc.strerror
        elif isinstance(exc, (mpd.ConnectionError, OSError)):
            msg = str(exc)
        if msg:
            self.main.error(msg[0].upper() + msg[1:] + ('.' if msg[-1] != '.' else ''))


class ProperConnection(Connection):
    def __init__(self, main):
        super().__init__(main)
        self.main = main
        self.conn = mpd.MPDClient()
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

