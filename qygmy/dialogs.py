
import os
import configparser

from PySide.QtCore import *
from PySide.QtGui import *

from .ui.infodialog import Ui_infodialog
from .ui.settings import Ui_settings


class Info(QDialog):
    def __init__(self, main):
        super().__init__(main)
        self.main = main
        self.ui = Ui_infodialog()
        self.ui.setupUi(self)

    def exec_(self, name, info, title):
        self.setWindowTitle(title)
        while self.ui.layout.count() > 0:
            w = self.ui.layout.takeAt(0)
            w.widget().hide()
            w.widget().deleteLater()
        d = self.main.fmt.info_dialog(name, info)
        for a, b in d:
            self.ui.layout.addRow(a, QLabel(b))
        self.adjustSize()
        super().exec_()


class Settings(QDialog):

    DEFAULTS = {
        'connection': {
            'host': 'localhost',
            'port': '6600',
            'password': '',
        },
        'format': {
            'window_title': (
                '[Qygmy]'
                '$if(%playing%, '
                '$if2(%title%,%filename%)'
                '$if(%artist%, / %artist%,),)'
            ),
            'progressbar': (
                '$if3('
                    '%playing%%paused%,'
                        '$time(%elapsed%)'
                        '$if($and(%total%,$gt(%total%,0)), / $time(%total%),),'
                    '%stopped%,Stopped,'
                    '%connected%,Connected,'
                    'Disconnected)'
            ),
            'current_song': (
                '<span style="font-size: big; font-weight: bold">'
                    '$if2(%title%,%filename%)</span><br>'
                '<span style="font-size: small">'
                    '%artist%</span><br>'
                '<span style="font-size: small">'
                    '%comment%$if($and(%comment%,%album%),&nbsp;&nbsp;/&nbsp;&nbsp;,)%album%</span>'
            ),
            'playlist_item': (
                '$if2(%title%,%filename%)'
                '$if(%artist%,'
                    '<span style="color: gray">&nbsp;&nbsp;/&nbsp;&nbsp;</span>%artist%,)'
                '$if(%album%%comment%,'
                    '<br><span style="color: gray; font-size: small">&nbsp;&nbsp;&nbsp;'
                    '%comment%'
                    '$if($and(%album%,%comment%),&nbsp;&nbsp;/&nbsp;&nbsp;,)'
                    '%album%</span>,)'
            ),
        },
        'gui': {},
    }

    PATH = os.path.expanduser(os.path.join(os.environ.get('XDG_CONFIG_HOME', '~/.config'), 'qygmy'))
    FILENAME = 'qygmy.conf'

    def __init__(self, main):
        super().__init__(main)
        self.main = main

        self.conf = configparser.ConfigParser(interpolation=None)
        self.conf.read_dict(self.DEFAULTS, '<defaults>')
        self.conf.read_dict(self.environ_conf(), '<MPD_HOST>')
        self.conf.read(os.path.join(self.PATH, self.FILENAME), 'utf-8')
        self.conf['connection']['host'] = self.conf['connection']['host'].strip()
        self.conf['connection']['port'] = self.validate_port(self.conf['connection']['port'].strip())
        self.setup_ui()

    def environ_conf(self):
        if 'MPD_HOST' in os.environ:
            env = os.environ['MPD_HOST']
            c = {}
            if '@' in env:
                c['password'], env = env.rsplit('@', 1)
            if ':' in env:
                env, c['port'] = env.rsplit(':', 1)
            if env:
                c['host'] = env
            return {'connection': c}
        return {}


    def setup_ui(self):
        self.ui = Ui_settings()
        self.ui.setupUi(self)
        self.conf_to_ui()

    def exec_(self):
        self.conf_to_ui()
        super().exec_()

    @Slot(QAbstractButton)
    def on_buttonbox_clicked(self, button):
        sb = self.ui.buttonbox.standardButton(button)
        if sb == QDialogButtonBox.Ok:
            self.ui_to_conf()
            self.save()
        elif sb == QDialogButtonBox.Cancel:
            self.conf_to_ui()
        elif sb == QDialogButtonBox.Apply:
            self.ui_to_conf()
            self.save()
        elif sb == QDialogButtonBox.RestoreDefaults:
            self.conf_to_ui(self.DEFAULTS)

    def conf_to_ui(self, conf=None):
        if conf is None:
            conf = self.conf
        c, f = conf['connection'], conf['format']
        self.ui.host.setText(c['host'])
        self.ui.port.setText(c['port'])
        self.ui.password.setText(c['password'])
        self.ui.window_title.setPlainText(f['window_title'])
        self.ui.progressbar.setPlainText(f['progressbar'])
        self.ui.current_song.setPlainText(f['current_song'])
        self.ui.playlist_item.setPlainText(f['playlist_item'])

    def ui_to_dict(self):
        return {
            'connection': {
                'host': self.ui.host.text().strip(),
                'port': self.validate_port(self.ui.port.text().strip()),
                'password': self.ui.password.text(),
            },
            'format': {
                'window_title': self.ui.window_title.toPlainText(),
                'progressbar': self.ui.progressbar.toPlainText(),
                'current_song': self.ui.current_song.toPlainText(),
                'playlist_item': self.ui.playlist_item.toPlainText(),
            },
        }

    def ui_to_conf(self):
        d = self.ui_to_dict()
        changed = set()
        for sect in ('connection', 'format'):
            for k in d[sect]:
                if d[sect][k] != self.conf[sect][k]:
                    changed.add(k)
                    self.conf[sect][k] = d[sect][k]
        if not {'host', 'port', 'password'}.isdisjoint(changed):
            self.main.srv.disconnect_mpd()
            self.main.connect_mpd()
        if not {'window_title', 'progressbar', 'current_song', 'playlist_item'}.isdisjoint(changed):
            self.main.fmt.clear_cache()
        if not {'window_title', 'current_song'}.isdisjoint(changed):
            self.main.update_current_song()
        if 'progressbar' in changed:
            self.main.update_progressbar()
        if 'playlist_item' in changed:
            self.main.srv.queue.refresh_format()
            self.main.srv.database.refresh_format()
            self.main.srv.playlists.refresh_format()
            self.main.srv.search.refresh_format()

    def save(self):
        try:
            os.makedirs(self.PATH, exist_ok=True)
            with open(os.path.join(self.PATH, self.FILENAME), 'w') as f:
                self.conf.write(f)
        except IOError as e:
            print(e.__class__.__name__ + ': ' + str(e))

    def validate_port(self, port):
        pi = None
        try:
            pi = int(port)
        except ValueError:
            pass
        if pi is not None and pi in range(1, 2**16):
            return port
        return self.DEFAULTS['connection']['port']

