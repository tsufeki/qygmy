
import os
import glob
import importlib.machinery
import configparser

from PySide.QtCore import *
from PySide.QtGui import *

from .ui.infodialog import Ui_infodialog
from .ui.settings import Ui_settings

import logging
log = logging.getLogger('qygmy')


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


def input_url(parent):
    url, ok = QInputDialog.getText(parent,
            QApplication.translate('input_url', 'Add URL'),
            QApplication.translate('input_url', 'URL:'))
    if ok and url:
        return url
    return None


class QygmyConfigParser(configparser.ConfigParser):

    def __init__(self, **kwargs):
        super().__init__(interpolation=None, **kwargs)

    def write(self, fp, space_around_delimiters=True):
        for sn, s in self.items():
            for k, v in s.items():
                if '\n' in v or '\r' in v:
                   s[k] = (''.join(('"', v.replace('\\', '\\\\')
                            .replace('\n', '\\n').replace('\r', '\\r'), '"')))
        super().write(fp, space_around_delimiters)
        self._unescape_nl()

    def read(self, filenames, encoding=None):
        r = super().read(filenames, encoding)
        self._unescape_nl()
        return r

    def read_file(self, f, source=None):
        super().read_file(f, source)
        self._unescape_nl()

    def _unescape_nl(self):
        for sn, s in self.items():
            for k, v in s.items():
                if len(v) > 2 and v[0] == v[-1] == '"':
                    s[k] = (v[1:-1].replace('\\n', '\n').replace('\\r', '\r')
                            .replace('\\\\', '\\'))


class Settings(QDialog):

    directory = 'qygmy'
    cfg_file = 'qygmy.conf'
    plugins_glob = 'tmplplugin_*.py'

    def __init__(self, main):
        super().__init__(main)
        self.main = main

        self.ui = Ui_settings()
        self.ui.setupUi(self)
        self.retranslate()

        self.conf = QygmyConfigParser()
        self.conf.read_dict(self.defaults, '<defaults>')
        self.conf.read_dict(self.environ_conf(), '<MPD_HOST>')
        self.cfg_dirs = [os.path.expanduser(os.environ.get('XDG_CONFIG_HOME', '~/.config'))]
        more = os.environ.get('XDG_CONFIG_DIRS', '')
        if more == '':
            more = '/etc/xdg'
        self.cfg_dirs.extend(d for d in more.split(':') if d and d[0] == '/')
        self.cfg_dirs = [os.path.join(d, self.directory) for d in self.cfg_dirs]
        cfg_files = [os.path.join(d, self.cfg_file) for d in self.cfg_dirs]
        try:
            self.conf.read(cfg_files, 'utf-8')
        except (configparser.Error, ValueError, OSError) as e:
            log.error('{}: {}'.format(e.__class__.__name__, e))
            self.conf._join_multiline_values()
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
                    '$if(%name%,[%name%] )'
                    '<span style="font-size: large; font-weight: bold">'
                        '$if2(%title%,%filename%)</span><br>'
                    '%artist%$if(%album%, \u2014 %album%)'
                ),
                'playlist_item': self.tr(
                    '$if(%name%,[%name%] )'
                    '$if(%artist%,%artist% \u2014 )'
                    '$if2(%title%,%filename%)'
                ),
                'sort_order': self.tr(
                    '%file%\n'
                    '%directory%\n'
                    '%playlist%\n'
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
        env = os.environ.get('MPD_HOST')
        if env:
            c = {}
            if '@' in env:
                c['password'], env = env.rsplit('@', 1)
            if ':' in env:
                env, c['port'] = env.rsplit(':', 1)
            if env:
                c['host'] = env
            if 'port' not in c:
                port = os.environ.get('MPD_PORT')
                if port:
                    c['port'] = port
            return {'connection': c}
        return {}

    def load_tmplplugins(self):
        self.tmplplugins = []
        for d in self.cfg_dirs:
            for f in sorted(glob.glob(os.path.join(d, self.plugins_glob))):
                try:
                    name = os.path.split(f)[1][:-3]
                    mod = importlib.machinery.SourceFileLoader(name, f).load_module()
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
        self.ui.sort_order.setPlainText(f['sort_order'])
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
                'sort_order': self.ui.sort_order.toPlainText(),
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
        if not {'window_title', 'progressbar', 'current_song', 'playlist_item', 'sort_order'}.isdisjoint(changed):
            self.main.fmt.clear_cache()
        if not {'window_title', 'current_song'}.isdisjoint(changed):
            self.main.update_current_song()
        if 'progressbar' in changed:
            self.main.update_progressbar()
        if 'playlist_item' in changed:
            self.main.srv.queue.refresh_format()
        if 'sort_order' in changed:
            self.main.srv.database.refresh()
            self.main.srv.playlists.refresh()
            self.main.srv.search.refresh()
        elif 'playlist_item' in changed:
            self.main.srv.database.refresh_format()
            self.main.srv.playlists.refresh_format()
            self.main.srv.search.refresh_format()
        if 'interval' in changed:
            self.main.srv.start_timer(int(self.conf['gui']['interval']))

    def save(self):
        try:
            cfg_dir = self.cfg_dirs[0]
            os.makedirs(cfg_dir, exist_ok=True)
            with open(os.path.join(cfg_dir, self.cfg_file), 'w', encoding='utf-8') as f:
                self.conf.write(f)
        except OSError as e:
            log.error('{}: {}'.format(e.__class__.__name__, e))

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

