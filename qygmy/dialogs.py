
import os
import glob
import importlib.machinery
import configparser

from PySide.QtCore import *
from PySide.QtGui import *

from .ui.infodialog import Ui_infodialog
from .ui.settings import Ui_settings

import logging
logger = logging.getLogger('qygmy')


class Info(QDialog):
    def __init__(self, main):
        super().__init__(main)
        self.main = main
        self.ui = Ui_infodialog()
        self.ui.setupUi(self)
        self.ui.icon_label.setPixmap(QIcon.fromTheme('dialog-information').pixmap(64, 64))

    def exec_(self, name, info, title):
        self.setWindowTitle(title)
        while self.ui.layout.count() > 0:
            w = self.ui.layout.takeAt(0)
            w.widget().hide()
            w.widget().deleteLater()
        d = self.main.fmt.info_dialog(name, info)
        for a, b in d:
            if b is None:
                self.ui.layout.addRow(QLabel(a))
            else:
                self.ui.layout.addRow(a, QLabel(b))
        self.adjustSize()
        super().exec_()


class Settings(QDialog):

    PATH = os.path.expanduser(os.path.join(os.environ.get('XDG_CONFIG_HOME', '~/.config'), 'qygmy'))
    FILENAME = 'qygmy.conf'
    PLUGINS = 'tmplplugin_*.py'

    def __init__(self, main):
        super().__init__(main)
        self.main = main

        self.ui = Ui_settings()
        self.ui.setupUi(self)
        self.retranslate()

        self.conf = configparser.ConfigParser(interpolation=None)
        self.conf.read_dict(self.defaults, '<defaults>')
        self.conf.read_dict(self.environ_conf(), '<MPD_HOST>')
        self.conf.read(os.path.join(self.PATH, self.FILENAME), 'utf-8')
        self.validate(self)
        self.conf_to_ui()
        self.load_tmplplugins()

    def retranslate(self):
        self.defaults = {
            'connection': {
                'host': 'localhost',
                'port': '6600',
                'password': '',
            },
            'format': {
                'window_title': self.tr(
                    'Qygmy'
                    '$if(%playing%, / '
                    '$if(%artist%,%artist% \u2014 )'
                    '$if2(%title%,%filename%))'
                ),
                'progressbar': self.tr(
                    '$if3('
                        '%playing%%paused%,'
                            '$time(%elapsed%)'
                            '$if($and(%total%,$gt(%total%,0)), / $time(%total%)),'
                        '%stopped%,Stopped,'
                        '%connected%,Connected,'
                        'Disconnected)'
                ),
                'current_song': self.tr(
                    '<span style="font-size: large; font-weight: bold">'
                        '$if2(%title%,%filename%)</span><br>'
                    '%artist%$if(%album%, \u2014 %album%)'
                ),
                'playlist_item': self.tr(
                    '$if(%artist%,%artist% \u2014 )'
                    '$if2(%title%,%filename%)'
                ),
            },
            'gui': {
                'autoscroll': '1',
                'interval': '500',
            },
            'guistate': {},
        }
        self.ui.retranslateUi(self)

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

    def load_tmplplugins(self):
        self.tmplplugins = []
        for plugin in sorted(glob.glob(os.path.join(self.PATH, self.PLUGINS))):
            try:
                name = os.path.split(plugin)[1][:-3]
                mod = importlib.machinery.SourceFileLoader(name, plugin).load_module()
                if mod:
                    self.tmplplugins.append(mod)
            except Exception as e:
                logger.error('{}: {}'.format(e.__class__.__name__, e))

    def __getitem__(self, section):
        return self.conf[section]

    def __contains__(self, section):
        return section in self.conf

    def exec_(self):
        self.conf_to_ui()
        super().exec_()

    @Slot(QAbstractButton)
    def on_buttonbox_clicked(self, button):
        sb = self.ui.buttonbox.standardButton(button)
        if sb == QDialogButtonBox.Ok:
            self.ui_to_conf()
            self.save()
            self.conf_to_ui()
        elif sb == QDialogButtonBox.Cancel:
            self.conf_to_ui()
        elif sb == QDialogButtonBox.Apply:
            self.ui_to_conf()
            self.save()
            self.conf_to_ui()
        elif sb == QDialogButtonBox.RestoreDefaults:
            self.conf_to_ui(self.defaults)

    def conf_to_ui(self, conf=None):
        if conf is None:
            conf = self.conf
        c, f, g = conf['connection'], conf['format'], conf['gui']
        self.ui.host.setText(c['host'])
        self.ui.port.setText(c['port'])
        self.ui.password.setText(c['password'])
        self.ui.window_title.setPlainText(f['window_title'])
        self.ui.progressbar.setPlainText(f['progressbar'])
        self.ui.current_song.setPlainText(f['current_song'])
        self.ui.playlist_item.setPlainText(f['playlist_item'])
        self.ui.autoscroll.setChecked(g['autoscroll'] == '1')
        self.ui.interval.setValue(int(g['interval']))

    def ui_to_dict(self):
        return {
            'connection': {
                'host': self.ui.host.text(),
                'port': self.ui.port.text(),
                'password': self.ui.password.text(),
            },
            'format': {
                'window_title': self.ui.window_title.toPlainText(),
                'progressbar': self.ui.progressbar.toPlainText(),
                'current_song': self.ui.current_song.toPlainText(),
                'playlist_item': self.ui.playlist_item.toPlainText(),
            },
            'gui': {
                'autoscroll': '1' if self.ui.autoscroll.isChecked() else '0',
                'interval': str(self.ui.interval.value()),
            },
        }

    def ui_to_conf(self):
        d = self.ui_to_dict()
        self.validate(d)
        changed = set()
        for sect in ('connection', 'format', 'gui'):
            for k in d[sect]:
                if d[sect][k] != self.conf[sect][k]:
                    changed.add(k)
                    self.conf[sect][k] = d[sect][k]
        if not {'host', 'port', 'password'}.isdisjoint(changed) and self.main.srv.state != 'disconnect':
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
        if 'interval' in changed:
            self.main.timer.stop()
            self.main.timer.start(int(self.conf['gui']['interval']))

    def save(self):
        try:
            os.makedirs(self.PATH, exist_ok=True)
            with open(os.path.join(self.PATH, self.FILENAME), 'w', encoding='utf-8') as f:
                self.conf.write(f)
        except OSError as e:
            logger.error('{}: {}'.format(e.__class__.__name__, e))

    @classmethod
    def validate_int(cls, string, imin, imax, default):
        string = string.strip()
        try:
            i = int(string)
            if imin <= i < imax:
                return string
        except ValueError:
            pass
        return default

    def validate(self, dct):
        c, g = dct['connection'], dct['gui']
        c['host'] = c['host'].strip()
        c['port'] = self.validate_int(c['port'], 1, 2**16, self.defaults['connection']['port'])
        g['autoscroll'] = '1' if g['autoscroll'] == '1' else '0'
        g['interval'] = self.validate_int(g['interval'], 100, 3600000, self.defaults['gui']['interval'])

