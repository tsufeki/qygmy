
from PySide.QtCore import *
from PySide.QtGui import *

from .formatter import Formatter
from .server import Server
from .browser import Browser
from .dialogs import Info, Settings
from .ui.main import Ui_main


class Qygmy(QMainWindow):

    def __init__(self):
        super().__init__()
        QTextCodec.setCodecForTr(QTextCodec.codecForName('UTF-8'))
        self.fmt = Formatter()
        self.srv = Server(self)
        self.info = Info(self)
        self.browser = Browser(self.srv, self.info)
        self.settings = Settings(self)
        self.timer = QTimer(self)
        self.setup_ui()
        self.connect_mpd()
        self.timer.timeout.connect(self.srv.update_state)
        self.timer.start(500)

    def connect_mpd(self):
        self.srv.connect_mpd('localhost', 6600, 'ka'*4)

    def setup_ui(self):
        self.ui = Ui_main()
        self.ui.setupUi(self)
        self.ui.current_song.setText(self.fmt.current_song('disconnect', {}))
        self.setup_icons()
        self.setup_widgets()
        self.setup_context_menu()
        self.setup_signals()

    def setup_icons(self):
        self.setWindowIcon(QIcon.fromTheme('applications-multimedia'))
        self.ui.settings_icon = QIcon.fromTheme('configure')
        self.ui.settings_icon_updating = QIcon.fromTheme('view-refresh')
        for action, icon in (
            ('previous', 'media-skip-backward'),
            ('play', 'media-playback-start'),
            ('pause', 'media-playback-pause'),
            ('stop', 'media-playback-stop'),
            ('next', 'media-skip-forward'),
            ('volume', 'audio-volume-high'),
            ('add', 'list-add'),
            ('remove', 'list-remove'),
            ('clear', 'edit-clear-list'),
            ('repeat', 'media-playlist-repeat'),
            ('shuffle', 'media-playlist-shuffle'),
            ('single', 'go-last'),
            ('consume', 'edit-delete-shred'),
            ('save', 'document-save'),
            ('settings', 'configure'),
            ('updatedb', 'view-refresh'),
            ('quit', 'application-exit'),
        ):
            getattr(self.ui, 'action_' + action).setIcon(QIcon.fromTheme(icon))

    def setup_widgets(self):
        self.ui.playback_toolbar.insertWidget(self.ui.action_volume, self.ui.progressbar)
        self.ui.queue_toolbar.insertWidget(self.ui.action_settings, self.ui.status)
        self.ui.queue_toolbar.insertSeparator(self.ui.action_settings)

        self.ui.queue.setup(self.srv.queue)

        self.ui.wa1 = QWidgetAction(self)
        self.ui.wa1.setDefaultWidget(self.ui.volume_label)
        self.ui.wa2 = QWidgetAction(self)
        self.ui.wa2.setDefaultWidget(self.ui.volume_slider)
        vm = QMenu(self)
        vm.addAction(self.ui.wa1)
        vm.addAction(self.ui.wa2)
        self.ui.volume_menu = vm
        vb = self.ui.playback_toolbar.widgetForAction(self.ui.action_volume)
        vb.setMenu(vm)
        vb.setPopupMode(QToolButton.InstantPopup)

    def setup_context_menu(self):
        cm = QMenu(self)
        for action in (
            'add', 'remove', 'clear', None,
            'repeat', 'shuffle', 'single', 'consume', None,
            'save', 'randomize', 'details', None,
            'statistics', 'updatedb', 'connect', 'disconnect', 'settings', None,
            'quit',
        ):
            if action is None:
                cm.addSeparator()
            else:
                cm.addAction(getattr(self.ui, 'action_' + action))
        self.ui.context_menu = cm

    def setup_signals(self):
        self.ui.action_play.triggered.connect(self.srv.play)
        self.ui.action_pause.triggered.connect(self.srv.pause)
        self.ui.action_stop.triggered.connect(self.srv.stop)
        self.ui.action_next.triggered.connect(self.srv.next)
        self.ui.action_previous.triggered.connect(self.srv.previous)
        self.ui.progressbar.clicked.connect(self.srv.times.send)
        self.srv.times.changed.connect(self.update_progressbar)
        self.srv.state.changed.connect(self.update_progressbar)
        self.srv.state.changed.connect(self.update_current_song)
        self.srv.current_song.changed.connect(self.update_progressbar)
        self.srv.current_song.changed.connect(self.update_current_song)
        self.srv.queue.current.changed.connect(self.update_status)
        self.srv.volume.changed.connect(self.ui.volume_slider.setValue)
        self.srv.volume.changed.connect(lambda v: self.ui.volume_label.setText(str(v)))
        self.ui.volume_slider.sliderMoved.connect(self.srv.volume.send)
        for v in ('repeat', 'shuffle', 'single', 'consume'):
            act = getattr(self.ui, 'action_' + v)
            getattr(self.srv, v).changed.connect(act.setChecked)
            def slot(varname):
                return lambda checked: self.on_bool_triggered(varname, checked)
            act.triggered[bool].connect(Slot(bool)(slot(v)))
        self.ui.action_add.triggered.connect(self.browser.show)
        self.ui.action_remove.triggered.connect(self.ui.queue.remove_selected)
        self.ui.action_clear.triggered.connect(self.srv.clear)
        self.ui.action_randomize.triggered.connect(self.srv.randomize_queue)
        self.ui.action_updatedb.triggered.connect(self.srv.updatedb)
        self.ui.action_connect.triggered.connect(self.connect_mpd)
        self.ui.action_disconnect.triggered.connect(self.srv.disconnect_mpd)
        self.ui.action_settings.triggered.connect(self.settings.exec_)
        self.ui.action_quit.triggered.connect(self.close)

    def error(self, message):
        QMessageBox.critical(self, self.tr('Error'), self.tr(message))

    def update_progressbar(self, *_):
        s = self.srv.state.value
        elapsed, total = self.srv.times.value
        text = self.fmt.progressbar(s, elapsed, total, self.srv.current_song.value)
        if elapsed > total:
            total = elapsed
        if (elapsed, total) == (0, 0):
            total = 1
        self.ui.progressbar.setRange(0, total)
        self.ui.progressbar.setValue(elapsed)
        self.ui.progressbar.setFormat(text)

    def update_current_song(self, *_):
        s, c = self.srv.state.value, self.srv.current_song.value
        self.ui.current_song.setText(self.fmt.current_song(s, c))
        self.ui.current_song.setToolTip(self.fmt.current_song_tooltip(s, c))
        self.setWindowTitle(self.fmt.window_title(s, c))

    def update_status(self, *_):
        self.ui.status.setText(self.fmt.status(self.srv.state.value,
                self.srv.queue.total_length, len(self.srv.queue)))

    def contextMenuEvent(self, e):
        e.accept()
        self.ui.action_details.setEnabled(self.ui.queue.details() is not None)
        self.ui.context_menu.popup(e.globalPos())

    @Slot(str)
    def on_state_changed(self, state):
        c = state != 'disconnect'
        self.ui.action_connect.setVisible(not c)
        self.ui.action_disconnect.setVisible(c)
        for action in ('previous', 'play', 'pause', 'stop', 'next', 'volume',
                'add', 'remove', 'clear', 'repeat', 'shuffle', 'single',
                'consume', 'updatedb', 'save', 'randomize', 'details'):
            getattr(self.ui, 'action_' + action).setEnabled(c)
        self.ui.action_play.setVisible(state != 'play')
        self.ui.action_pause.setVisible(state == 'play')

    def on_bool_triggered(self, varname, checked):
        var = getattr(self.srv, varname)
        getattr(self.ui, 'action_' + varname).setChecked(var.value)
        var.send(checked)

    @Slot(bool)
    def on_updating_db_changed(self, updating):
        if updating:
            self.ui.action_settings.setIcon(self.ui.settings_icon_updating)
        else:
            self.ui.action_settings.setIcon(self.ui.settings_icon)

    @Slot()
    def on_action_details_triggered(self):
        d = self.ui.queue.details()
        if d is not None:
            self.info.show_dialog('details', d)

    @Slot()
    def on_action_statistics_triggered(self):
        self.info.show_dialog('statistics', self.srv.statistics())

    @Slot()
    def on_action_save_triggered(self):
        while True:
            name, ok = QInputDialog.getText(self,
                    self.tr('Save current playlist'),
                    self.tr('Playlist name:'))
            if not ok:
                break
            if not name:
                self.error('You have to provide a name.')
            elif self.srv.queue.save(name) is False:
                ans = QMessageBox.question(self, self.tr('Error'),
                        self.tr('Playlist with such name already exists. '
                        'Do you want to replace\u00a0it?'),
                        QMessageBox.Yes | QMessageBox.No)
                if ans == QMessageBox.Yes:
                    self.srv.queue.save(name, True)
                break
            else: break


def main():
    import sys
    app = QApplication(sys.argv)
    m = Qygmy()
    m.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

