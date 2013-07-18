
from PySide.QtCore import *
from PySide.QtGui import *

from .formatter import Formatter
from .server import Server
from .browser import Browser
from .dialogs import Info, Settings
from .ui.main import Ui_main
from .__version__ import version


class Qygmy(QMainWindow):

    def __init__(self):
        super().__init__()
        QTextCodec.setCodecForTr(QTextCodec.codecForName('UTF-8'))
        self.settings = Settings(self)
        self.fmt = Formatter(self.settings)
        self.srv = Server(self)
        self.info = Info(self)
        self.browser = Browser(self)
        self.timer = QTimer(self)
        self.setup_ui()
        self.timer.start(int(self.settings['gui']['interval']))

    def connect_mpd(self):
        self.srv.connect_mpd(
            self.settings['connection']['host'],
            int(self.settings['connection']['port']),
            self.settings['connection']['password'])

    def create_eventloop_timer(self, slot):
        t = QTimer(self)
        t.setInterval(0)
        t.setSingleShot(True)
        t.timeout.connect(slot)
        return t

    def setup_ui(self):
        self.ui = Ui_main()
        self.ui.setupUi(self)
        self.ui.current_song.setText(self.fmt.current_song('disconnect', {}))
        self.setup_icons()
        self.setup_widgets()

        self.busy_stack = 0
        self.busy_stack_real = 0
        self.notbusy_timer = self.create_eventloop_timer(self.not_busy2)
        self.scroll_timer = self.create_eventloop_timer(self.scroll_to_current2)
        self.setup_signals()

        try:
            if 'main_geometry' in self.settings['guistate']:
                self.restoreGeometry(QByteArray.fromBase64(self.settings['guistate']['main_geometry']))
        except:
            pass

    def setup_icons(self):
        self.setWindowIcon(QIcon.fromTheme('applications-multimedia'))
        self.ui.settings_icon = QIcon.fromTheme('configure')
        self.ui.settings_icon_updating = QIcon.fromTheme('view-refresh')
        for e, icon in (
            ('previous', 'media-skip-backward'),
            ('play', 'media-playback-start'),
            ('pause', 'media-playback-pause'),
            ('stop', 'media-playback-stop'),
            ('next', 'media-skip-forward'),
            ('volume', 'audio-volume-high'),
            ('add', 'list-add'),
            ('remove', 'list-remove'),
            ('clear', 'edit-clear-list'),
            ('copy', 'edit-copy'),
            ('repeat', 'media-playlist-repeat'),
            ('shuffle', 'media-playlist-shuffle'),
            ('single', 'go-last'),
            ('consume', 'edit-delete-shred'),
            ('highprio', 'flag-red'),
            ('save', 'document-save'),
            ('details', 'dialog-information'),
            ('settings', 'configure'),
            ('updatedb', 'view-refresh'),
            ('about', 'applications-multimedia'),
            ('quit', 'application-exit'),
            ('louder', 'audio-volume-high'),
            ('quieter', 'audio-volume-low'),
            ('playback_menu', 'media-playback-start'),
            ('playlist_menu', 'text-plain'),
        ):
            getattr(self.ui, e).setIcon(QIcon.fromTheme(icon))

    def setup_widgets(self):
        self.ui.playback_toolbar.insertWidget(self.ui.volume, self.ui.progressbar)
        self.ui.queue_toolbar.insertWidget(self.ui.settings, self.ui.status)
        self.ui.queue_toolbar.insertSeparator(self.ui.settings)
        self.ui.queue.setup(self.srv.queue)

        self.ui.wa1 = QWidgetAction(self)
        self.ui.wa1.setDefaultWidget(self.ui.volume_label)
        self.ui.wa2 = QWidgetAction(self)
        self.ui.wa2.setDefaultWidget(self.ui.volume_slider)
        vm = QMenu(self)
        vm.addAction(self.ui.wa1)
        vm.addAction(self.ui.wa2)
        self.ui.volume_popup = vm
        vb = self.ui.playback_toolbar.widgetForAction(self.ui.volume)
        vb.setMenu(vm)
        vb.setPopupMode(QToolButton.InstantPopup)

    def setup_signals(self):
        self.timer.timeout.connect(self.srv.update_state)
        self.ui.play.triggered.connect(self.srv.play)
        self.ui.pause.triggered.connect(self.srv.pause)
        self.ui.stop.triggered.connect(self.srv.stop)
        self.ui.next.triggered.connect(self.srv.next)
        self.ui.previous.triggered.connect(self.srv.previous)
        self.ui.progressbar.clicked.connect(self.srv.times.send)
        self.srv.times.changed.connect(self.update_progressbar)
        self.srv.state.changed.connect(self.update_progressbar)
        self.srv.state.changed.connect(self.update_current_song)
        self.srv.current_song.changed.connect(self.update_progressbar)
        self.srv.current_song.changed.connect(self.update_current_song)
        self.srv.current_song.changed2.connect(self.scroll_to_current)
        self.srv.queue.current.changed.connect(self.update_status)
        self.srv.volume.changed.connect(self.ui.volume_slider.setValue)
        self.srv.volume.changed.connect(lambda v: self.ui.volume_label.setText(str(v)))
        self.ui.volume_slider.sliderMoved.connect(self.srv.volume.send)
        self.ui.louder.triggered.connect(lambda v=self.srv.volume: v.send(min(v.value+1, 100)))
        self.ui.quieter.triggered.connect(lambda v=self.srv.volume: v.send(max(v.value-1, 0)))
        for v in ('repeat', 'shuffle', 'single', 'consume'):
            act = getattr(self.ui, v)
            var = getattr(self.srv, v)
            def slot(checked, act=act, var=var):
                act.setChecked(var.value)
                var.send(checked)
            act.triggered[bool].connect(slot)
            var.changed.connect(act.setChecked)
        self.ui.add.triggered.connect(self.browser.show)
        self.ui.add.triggered.connect(self.browser.activateWindow)
        self.ui.remove.triggered.connect(self.ui.queue.remove_selected)
        self.ui.clear.triggered.connect(self.srv.clear)
        self.ui.copy.triggered.connect(self.ui.queue.copy_selected)
        self.ui.randomize.triggered.connect(self.srv.randomize_queue)
        self.ui.reverse.triggered.connect(self.srv.queue.reverse)
        self.ui.updatedb.triggered.connect(self.srv.updatedb)
        self.ui.connect.triggered.connect(self.connect_mpd)
        self.ui.disconnect.triggered.connect(self.srv.disconnect_mpd)
        self.ui.settings.triggered.connect(self.settings.exec_)
        self.ui.quit.triggered.connect(self.close)
        self.ui.highprio.triggered.connect(lambda: self.ui.queue.set_priority(1))
        self.ui.normprio.triggered.connect(lambda: self.ui.queue.set_priority(0))

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

    def scroll_to_current(self, new_song, old_song):
        pnew, pold = new_song.get('file', ''), old_song.get('file', '')
        pos = int(new_song.get('pos', '-1'))
        if (pos < 0 or pnew == pold or not pnew or
                self.srv.state.value not in ('play', 'pause') or
                self.settings['gui']['autoscroll'] != '1'):
            return
        self.scroll_pos = pos
        self.scroll_timer.start()

    def scroll_to_current2(self):
        pos = self.scroll_pos
        index = self.srv.queue.index(pos, 0)
        if not self.ui.queue.rect().contains(self.ui.queue.visualRect(index)):
            self.ui.queue.scrollTo(index, QAbstractItemView.PositionAtCenter)

    def contextMenuEvent(self, e):
        e.accept()
        self.ui.highprio.setEnabled(self.ui.queue.can_set_priority(1))
        self.ui.normprio.setEnabled(self.ui.queue.can_set_priority(0))
        self.ui.copy.setEnabled(self.ui.queue.can_copy())
        self.ui.details.setEnabled(self.ui.queue.details() is not None)
        self.ui.context_menu.popup(e.globalPos())

    def closeEvent(self, e):
        self.srv.disconnect_mpd()
        self.settings['guistate']['main_geometry'] = str(self.saveGeometry().toBase64())
        self.browser.close()
        self.settings.save()
        super().closeEvent(e)

    @Slot(str)
    def on_state_changed(self, state):
        c = state != 'disconnect'
        self.ui.connect.setVisible(not c)
        self.ui.disconnect.setVisible(c)
        self.ui.play.setVisible(state != 'play')
        self.ui.pause.setVisible(state == 'play')
        for e in ('previous', 'play', 'pause', 'stop', 'next', 'volume',
                'add', 'clear', 'repeat', 'shuffle', 'single', 'consume',
                'updatedb', 'save', 'randomize', 'details', 'statistics',
                'louder', 'quieter', 'reverse',
                'playback_menu', 'volume_menu', 'playlist_menu', 'outputs_menu'):
            getattr(self.ui, e).setEnabled(c)
        self.on_queue_selection_changed()

    @Slot(bool)
    def on_updating_db_changed(self, updating):
        if updating:
            self.ui.settings.setIcon(self.ui.settings_icon_updating)
        else:
            self.ui.settings.setIcon(self.ui.settings_icon)

    @Slot()
    def on_outputs_menu_aboutToShow(self):
        self.ui.outputs_menu.clear()
        for name, oid, enabled in self.srv.outputs():
            a = QAction(name, self.ui.outputs_menu)
            a.setCheckable(True)
            a.setChecked(enabled)
            a.triggered[bool].connect(lambda enable, oid=oid: self.srv.enable_output(oid, enable))
            self.ui.outputs_menu.addAction(a)

    @Slot()
    def on_queue_selection_changed(self):
        self.ui.remove.setEnabled(self.srv.state.value != 'disconnect' and
                self.ui.queue.can_remove())

    @Slot()
    def on_details_triggered(self):
        d = self.ui.queue.details()
        if d is not None:
            self.info.exec_('details', d, 'Details')

    @Slot()
    def on_statistics_triggered(self):
        self.info.exec_('statistics', self.srv.statistics(), 'MPD statistics')

    @Slot()
    def on_save_triggered(self):
        name = None
        while True:
            name, ok = QInputDialog.getText(self,
                    self.tr('Save current playlist'),
                    self.tr('Playlist name:'),
                    text=name if name else self.srv.playlists.NEW_PLAYLIST_NAME)
            if not ok:
                break
            if not name:
                self.error('You have to provide a name.')
            elif self.srv.playlists.save_queue(name) is False:
                ans = QMessageBox.question(self, self.tr('Error'),
                        self.tr('Playlist with such name already exists. '
                        'Do you want to replace it?'),
                        QMessageBox.Yes | QMessageBox.No)
                if ans == QMessageBox.Yes:
                    self.srv.playlists.save_queue(name, True)
                    break
            else: break

    @Slot()
    def on_aboutqt_triggered(self):
        QMessageBox.aboutQt(self)

    @Slot()
    def on_about_triggered(self):
        QMessageBox.about(
            self, self.tr('About Qygmy'),
            self.tr(
                '<h2>Qygmy</h2>'
                '<p>version {version}</p>'
                '<p>Simple MPD client written in Python and Qt/PySide.</p>'
                '<p><a href="https://github.com/tsufeki/qygmy">https://github.com/tsufeki/qygmy</a></p>'
            ).format(version=version))

    def busy(self):
        self.busy_stack_real += 1
        self.busy_stack += 1
        QApplication.setOverrideCursor(Qt.BusyCursor)

    def not_busy(self):
        self.busy_stack -= 1
        self.notbusy_timer.start()

    def not_busy2(self):
        while self.busy_stack_real > self.busy_stack:
            self.busy_stack_real -= 1
            QApplication.restoreOverrideCursor()


def main(translations_path=None):
    import sys
    import os

    if translations_path is None:
        translations_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'translations')

    app = QApplication(sys.argv)
    locale = QLocale.system().name()

    qt_tr = QTranslator()
    if qt_tr.load('qt_' + locale, QLibraryInfo.location(QLibraryInfo.TranslationsPath)):
        app.installTranslator(qt_tr)

    qygmy_tr = QTranslator()
    if qygmy_tr.load('qygmy_' + locale, translations_path):
        app.installTranslator(qygmy_tr)

    m = Qygmy()
    m.show()
    m.connect_mpd()
    # XXX: TODO: FIXME:
    os._exit(app.exec_())
    #sys.exit(app.exec_())

if __name__ == '__main__':
    main()

