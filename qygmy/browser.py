
from PySide.QtCore import *
from PySide.QtGui import *

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
        self.ui.database.setup(self.srv.database)
        self.srv.database.current.changed.connect(self.ui.dbpath.set_path)
        self.ui.dbpath.clicked.connect(self.srv.database.cd)
        self.ui.playlists.setup(self.srv.playlists)
        self.srv.playlists.current.changed.connect(self.ui.plpath.set_path)
        self.ui.plpath.clicked.connect(self.srv.playlists.cd)
        self.ui.search_results.setup(self.srv.search)
        self.ui.search_button.setDefaultAction(self.ui.search)
        self.srv.state.changed.connect(self.on_state_changed)
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
        self.setWindowIcon(QIcon.fromTheme('list-add'))
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

    def closeEvent(self, e):
        self.main.settings['guistate']['browser_geometry'] = str(self.saveGeometry().toBase64())
        self.main.settings['guistate']['browser_tab'] = str(self.ui.tabs.currentIndex())
        super().closeEvent(e)

    def contextMenuEvent(self, e):
        e.accept()
        self.ui.add.setVisible(self.current_view.can_add_to_queue())
        self.ui.remove.setVisible(self.current_view.can_remove())
        self.ui.rename.setVisible(self.current_view.can_rename())
        self.ui.copy.setVisible(self.current_view.can_copy())
        self.ui.details.setVisible(self.current_view.details() is not None)
        self.ui.context_menu.popup(e.globalPos())

    def on_state_changed(self, state):
        c = state != 'disconnect'
        for act in ('search', 'add', 'addplay', 'replace', 'replaceplay',
                'remove', 'rename', 'copy', 'details', 'updatedb'):
            getattr(self.ui, act).setEnabled(c)
        self.ui.dbpath.setEnabled(c)
        self.ui.plpath.setEnabled(c)
        self.ui.what.setEnabled(c)
        self.ui.query.setEnabled(c)

    @Slot()
    def on_search_triggered(self):
        self.srv.search.cd((self.ui.what.currentIndex(), self.ui.query.text()))

    @Slot()
    def on_add_triggered(self, play=False, replace=False):
        self.current_view.add_selected_to_queue(play, replace)

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
    def on_remove_triggered(self):
        self.current_view.remove_selected()

    @Slot()
    def on_rename_triggered(self):
        self.current_view.rename_selected()

    @Slot()
    def on_copy_triggered(self):
        self.current_view.copy_selected()

    @Slot()
    def on_details_triggered(self):
        d = self.current_view.details()
        if d is not None:
            self.main.info.exec_('details', d, self.tr('Details'))

