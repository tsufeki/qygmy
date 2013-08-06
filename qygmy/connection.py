
import re
import functools

import mpd
from PySide.QtCore import *

import logging
log = logging.getLogger('qygmy')


class State(QObject):

    default = None
    changed = None
    changed2 = None

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
            log.debug('{} changed: {!r} -> {!r}'.format(self.objectName(), old_value, new_value))
            self.changed.emit(self._value)
            self.changed2.emit(self._value, old_value)

    def send(self, value):
        pass

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
    def create(cls, parent, name, init, send_cmd=None):
        if not callable(send_cmd):
            send_cmd = lambda v, s=send_cmd or name: getattr(parent.conn, s)(v)
        class CompleteState(cls):
            default = init
            changed = Signal(type(init))
            changed2 = Signal(type(init), type(init))
            def send(self, value):
                value = self.prepare(value)
                mpd_cmd(lambda p, v: send_cmd(v))(parent, value)
        s = CompleteState()
        s.setObjectName(name)
        s.setParent(parent)
        setattr(parent, name, s)


class BoolState(State):
    def normalize(self, value):
        return value in (True, 1, '1')

    def prepare(self, value):
        return int(self.normalize(value))

    @classmethod
    def create(cls, parent, name, init=False, send_cmd=None):
        super().create(parent, name, init, send_cmd)


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


def mpd_cmd(method=None, *, ignore_conn=False, fallback=None, refresh=True):
    if method is None:
        def decorator(method):
            return mpd_cmd(method, ignore_conn=ignore_conn, fallback=fallback,
                    refresh=refresh)
        return decorator
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        ret = fallback
        if self.state.value != 'disconnect' or ignore_conn:
            try:
                ret = method(self, *args, **kwargs)
            except (mpd.MPDError, OSError) as e:
                self.handle_error(e)
        if refresh:
            self.refresh()
        return ret
    return wrapper


def simple_mpd(name, *args):
    return mpd_cmd(lambda self: getattr(self.conn, name)(*args))


def not_callable(*args):
    raise TypeError("Not callable")


def mpd_cmdlist_context_manager(connection):
    class MPDCommandList:
        conn = connection

        def __enter__(self):
            self.conn.command_list_ok_begin()
            return self

        def __exit__(self, *exc):
            self.retval = self.conn.command_list_end()
    return MPDCommandList


class Connection:

    MPD_COMMAND_ERROR_RE = re.compile(r'^\[([0-9]+)@([0-9]+)\] \{([^}]*)\} (.*)$')
    MAX_MPD_ARGUMENTS = 36

    def parse_exception(self, exc):
        m = self.MPD_COMMAND_ERROR_RE.match(exc.args[0])
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
        log.error('{}: {}'.format(exc.__class__.__name__, exc))
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
        self.mpd_cmdlist = mpd_cmdlist_context_manager(self.conn)
        State.create(self, 'state', 'disconnect', not_callable)

    def refresh(self):
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
    def mpd_cmdlist(self):
        return self.parent.mpd_cmdlist

    @property
    def state(self):
        return self.parent.state

    def refresh(self):
        self.parent.refresh()

