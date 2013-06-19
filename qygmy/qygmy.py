
from PySide.QtCore import *
from PySide.QtGui import *

from .formatter import Formatter
from .server import Server
from .browser import Browser
from .dialogs import Details, Settings
from .uiutils import RichTextDelegate
from .ui.main import Ui_main


class Qygmy(QMainWindow):

    def __init__(self):
        super().__init__()
        QTextCodec.setCodecForTr(QTextCodec.codecForName('UTF-8'))
        self.fmt = Formatter()
        self.p = Server(self.fmt)
        self.p.setParent(self)
        self.browser = Browser(self, self.fmt)
        self.details = Details(self, self.fmt)
        self.settings = Settings(self)
        self.timer = QTimer(self)
        self.setup_ui()
        self.connect_mpd()
        self.timer.timeout.connect(self.p.update)
        self.timer.start(500)

    def connect_mpd(self):
        self.p.connect_mpd('localhost', 6600, 'ka'*4)

    def setup_ui(self):
        self.ui = Ui_main()
        self.ui.setupUi(self)
        self.ui.current_song.setText(self.fmt.current_song({}))
        self.setup_icons()
        self.setup_widgets()
        self.setup_playlist()
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
            ('settings', 'configure'),
            ('updatedb', 'view-refresh'),
            ('quit', 'application-exit'),
        ):
            getattr(self.ui, 'action_' + action).setIcon(QIcon.fromTheme(icon))

    def setup_widgets(self):
        self.ui.playback_toolbar.insertWidget(self.ui.action_volume, self.ui.progressbar)
        self.ui.playlist_toolbar.insertWidget(self.ui.action_settings, self.ui.status)

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

    def setup_playlist(self):
        self.ui.delegate = RichTextDelegate()
        self.ui.playlist.setModel(self.p.playlist)
        self.ui.playlist.setItemDelegate(self.ui.delegate)

        h = self.ui.playlist.header()
        h.setResizeMode(0, QHeaderView.Stretch)
        for i in range(1,h.count()):
            h.setResizeMode(i, QHeaderView.ResizeToContents)

    def setup_context_menu(self):
        cm = QMenu(self)
        for action in (
            'add', 'remove', 'clear', None,
            'repeat', 'shuffle', 'single', 'consume', None,
            'save', 'details', None,
            'updatedb', 'connect', 'disconnect', 'settings', None,
            'quit',
        ):
            if action is None:
                cm.addSeparator()
            else:
                cm.addAction(getattr(self.ui, 'action_' + action))
        self.ui.context_menu = cm

    def setup_signals(self):
        self.ui.action_play.triggered.connect(self.p.play)
        self.ui.action_pause.triggered.connect(self.p.pause)
        self.ui.action_stop.triggered.connect(self.p.stop)
        self.ui.action_next.triggered.connect(self.p.next)
        self.ui.action_previous.triggered.connect(self.p.previous)
        self.ui.progressbar.clicked.connect(self.p.times.send)
        self.p.volume.changed.connect(self.ui.volume_slider.setValue)
        self.p.volume.changed.connect(lambda v: self.ui.volume_label.setText(str(v)))
        self.ui.volume_slider.sliderMoved.connect(self.p.volume.send)
        for v in ('repeat', 'shuffle', 'single', 'consume'):
            act = getattr(self.ui, 'action_' + v)
            getattr(self.p, v).changed.connect(act.setChecked)
            def slot(varname):
                return lambda checked: self.on_bool_triggered(varname, checked)
            act.triggered[bool].connect(Slot(bool)(slot(v)))
        self.ui.action_add.triggered.connect(self.browser.show)
        self.ui.action_clear.triggered.connect(self.p.clear)
        self.ui.action_updatedb.triggered.connect(self.p.updatedb)
        self.ui.action_connect.triggered.connect(self.connect_mpd)
        self.ui.action_disconnect.triggered.connect(self.p.disconnect_mpd)
        self.ui.action_quit.triggered.connect(self.close)

    def contextMenuEvent(self, e):
        e.accept()
        ind = [i.row()
                for i in self.ui.playlist.selectedIndexes()
                if i.column() == 0]
        self.ui.action_details.setEnabled(len(ind) == 1)
        self.ui.context_menu.popup(e.globalPos())

    @Slot(str)
    def on_state_changed(self, state):
        c = state != 'disconnect'
        self.ui.action_connect.setVisible(not c)
        self.ui.action_disconnect.setVisible(c)
        for action in ('previous', 'play', 'pause', 'stop', 'next', 'volume',
                'add', 'remove', 'clear', 'repeat', 'shuffle', 'single',
                'consume', 'updatedb', 'save', 'details'):
            getattr(self.ui, 'action_' + action).setEnabled(c)
        if state in ('disconnect', 'stop'):
            self.ui.progressbar.setRange(0, 1)
            self.ui.progressbar.setValue(0)
            self.ui.progressbar.setFormat(self.fmt.progressbar_notplaying(state))
        self.ui.action_play.setVisible(state != 'play')
        self.ui.action_pause.setVisible(state == 'play')

    @Slot(tuple)
    def on_times_changed(self, times):
        if self.p.state.value in ('play', 'pause'):
            text, e, t = self.fmt.progressbar(times)
            self.ui.progressbar.setRange(0, t)
            self.ui.progressbar.setValue(e)
            self.ui.progressbar.setFormat(text)

    @Slot(dict)
    def on_current_song_changed(self, song):
        self.ui.current_song.setText(self.fmt.current_song(song))
        self.setWindowTitle(self.fmt.main_window_title(song))

    @Slot(QModelIndex)
    def on_playlist_doubleClicked(self, index):
        if 0 <= index.row() < len(self.p.playlist):
            self.p.current_pos.send(index.row())

    @Slot()
    def on_action_remove_triggered(self):
        positions = [i.row()
                for i in self.ui.playlist.selectedIndexes()
                if i.column() == 0]
        self.p.remove(positions)

    def on_bool_triggered(self, varname, checked):
        var = getattr(self.p, varname)
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
        ind = [i.row()
                for i in self.ui.playlist.selectedIndexes()
                if i.column() == 0]
        if len(ind) == 1:
            self.details.show_details(self.p.playlist.songs[ind[0]])

    @Slot()
    def on_action_settings_triggered(self):
        self.settings.exec_()

    @Slot()
    def on_action_save_triggered(self):
        while True:
            name, ok = QInputDialog.getText(self,
                    self.tr('Save current playlist'),
                    self.tr('Playlist name:'))
            if ok:
                if not name:
                    QMessageBox.critical(self, self.tr('Error'),
                            self.tr('You have to provide a name.'))
                elif self.p.playlists_save(name) is False:
                    QMessageBox.critical(self, self.tr('Error'),
                            self.tr('Playlist with such name already exists.'))
                else: break
            else: break


def main():
    import sys
    app = QApplication(sys.argv)
    main = Qygmy()
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

