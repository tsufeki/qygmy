
from PySide.QtCore import *
from PySide.QtGui import *

from .dialogs import input_url
from .ui.browser import Ui_browser


class Browser(QMainWindow):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.srv = main.srv
        self.setup_ui()

    def setup_ui(self):
        self.ui = Ui_browser()
        self.ui.setupUi(self)
        self.setup_icons()
        self.ui.statusbar.addWidget(self.ui.status, 1)
        self.ui.database.setup(self.srv.database)
        self.srv.database.current.changed.connect(self.ui.dbpath.set_path)
        self.srv.database.current.changed.connect(self.update_status)
        self.ui.dbpath.clicked.connect(self.srv.database.cd)
        self.ui.playlists.setup(self.srv.playlists)
        self.srv.playlists.current.changed.connect(self.ui.plpath.set_path)
        self.srv.playlists.current.changed.connect(self.update_status)
        self.ui.plpath.clicked.connect(self.srv.playlists.cd)
        self.ui.search_results.setup(self.srv.search)
        self.srv.search.current.changed.connect(self.update_status)
        self.ui.search_button.setDefaultAction(self.ui.search)
        self.ui.what.setModel(self.srv.search.search_tags)
        self.ui.what.model().modelReset.connect(lambda: self.ui.what.setCurrentIndex(0))
        self.srv.state.changed.connect(self.on_state_changed)
        self.srv.state.changed.connect(self.update_status)
        self.ui.tabs.currentChanged.connect(self.update_status)
        self.ui.updatedb.triggered.connect(self.srv.updatedb)
        self.ui.close.triggered.connect(self.close)

        try:
            if 'browser_geometry' in self.main.settings['guistate']:
                self.restoreGeometry(QByteArray.fromBase64(self.main.settings['guistate']['browser_geometry']))
            if ('browser_tab' in self.main.settings['guistate'] and
                    0 <= int(self.main.settings['guistate']['browser_tab']) < self.ui.tabs.count()):
                self.ui.tabs.setCurrentIndex(int(self.main.settings['guistate']['browser_tab']))
        except:
            pass

    def setup_icons(self):
        self.setWindowIcon(self.main.get_icon())
        for action, icon in (
            ('add', 'list-add'),
            ('remove', 'edit-delete'),
            ('close', 'window-close'),
            ('search', 'edit-find'),
            ('copy', 'edit-copy'),
            ('updatedb', 'view-refresh'),
        ):
            getattr(self.ui, action).setIcon(QIcon.fromTheme(icon))
        for i, icon in enumerate(['folder-sound', 'document-multiple', 'edit-find']):
            self.ui.tabs.setTabIcon(i, QIcon.fromTheme(icon))
        self.ui.dbpath.set_root_icon('folder-sound')
        self.ui.plpath.set_root_icon('document-multiple')

    @property
    def current_view(self):
        i = self.ui.tabs.currentIndex()
        if i == 0: return self.ui.database
        elif i == 1: return self.ui.playlists
        elif i == 2: return self.ui.search_results

    def update_status(self, *_):
        self.ui.status.setText(self.main.fmt.browser_status(self.srv.state.value,
                self.current_view.model().total_length, len(self.current_view.model())))

    def closeEvent(self, e):
        self.main.settings['guistate']['browser_geometry'] = str(self.saveGeometry().toBase64())
        self.main.settings['guistate']['browser_tab'] = str(self.ui.tabs.currentIndex())
        super().closeEvent(e)

    def contextMenuEvent(self, e):
        e.accept()
        can_add = self.current_view.can_add_to_queue()
        for act in ('add', 'addplay', 'replace', 'replaceplay', 'addhighprio'):
            getattr(self.ui, act).setVisible(can_add)
        self.ui.remove.setVisible(self.current_view.can_remove())
        self.ui.rename.setVisible(self.current_view.can_rename())
        self.ui.copy.setVisible(self.current_view.can_copy())
        self.ui.addurl.setVisible(self.current_view.model().can_add_url())
        self.ui.details.setVisible(self.current_view.details() is not None)
        self.ui.context_menu.popup(e.globalPos())

    def on_state_changed(self, state):
        c = state != 'disconnect'
        for act in ('search', 'add', 'addplay', 'replace', 'replaceplay',
                'addhighprio', 'remove', 'rename', 'copy', 'addurl', 'details',
                'updatedb'):
            getattr(self.ui, act).setEnabled(c)
        self.ui.dbpath.setEnabled(c)
        self.ui.plpath.setEnabled(c)
        self.ui.what.setEnabled(c)
        self.ui.query.setEnabled(c)

    @Slot()
    def on_search_triggered(self):
        self.srv.search.cd((self.ui.what.itemData(self.ui.what.currentIndex()),
            self.ui.query.text()))

    @Slot()
    def on_add_triggered(self, play=False, replace=False, priority=0):
        self.current_view.add_selected_to_queue(play, replace, priority)

    @Slot()
    def on_addplay_triggered(self):
        self.on_add_triggered(True)

    @Slot()
    def on_replace_triggered(self):
        self.on_add_triggered(False, True)

    @Slot()
    def on_replaceplay_triggered(self):
        self.on_add_triggered(True, True)

    @Slot()
    def on_addhighprio_triggered(self):
        self.on_add_triggered(priority=1)

    @Slot()
    def on_remove_triggered(self):
        self.current_view.remove_selected()

    @Slot()
    def on_rename_triggered(self):
        self.current_view.rename_selected()

    @Slot()
    def on_copy_triggered(self):
        self.current_view.copy_selected()

    @Slot()
    def on_addurl_triggered(self):
        if self.current_view.model().can_add_url():
            url = input_url(self)
            if url:
                self.current_view.model().add_url(url)

    @Slot()
    def on_details_triggered(self):
        d = self.current_view.details()
        if d is not None:
            self.main.info.exec_('details', d, self.tr('Details'))

