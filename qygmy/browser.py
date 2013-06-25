
from PySide.QtCore import *
from PySide.QtGui import *

from .ui.browser import Ui_browser


class Browser(QMainWindow):
    def __init__(self, main):
        super().__init__()
        self.main = main
        self.srv = main.srv
        self.setup_ui()
        self.setAttribute(Qt.WA_QuitOnClose, False)

    def setup_ui(self):
        self.ui = Ui_browser()
        self.ui.setupUi(self)
        self.setup_icons()
        self.setup_database()
        self.setup_playlists()
        self.setup_search()
        self.srv.state.changed.connect(self.on_state_changed)

        if 'browser_geometry' in self.main.settings['gui']:
            self.restoreGeometry(QByteArray.fromBase64(self.main.settings['gui']['browser_geometry']))
        if ('browser_tab' in self.main.settings['gui'] and
                0 <= int(self.main.settings['gui']['browser_tab']) < self.ui.tabs.count()):
            self.ui.tabs.setCurrentIndex(int(self.main.settings['gui']['browser_tab']))

    def setup_icons(self):
        self.setWindowIcon(QIcon.fromTheme('list-add'))
        for action, icon in (
            ('add', 'list-add'),
            ('remove', 'edit-delete'),
            ('close', 'window-close'),
            ('dbroot', 'folder-sound'),
            ('plroot', 'document-multiple'),
            ('search', 'edit-find'),
        ):
            getattr(self.ui, action).setIcon(QIcon.fromTheme(icon))
        for i, icon in enumerate(['folder-sound', 'document-multiple', 'edit-find']):
            self.ui.tabs.setTabIcon(i, QIcon.fromTheme(icon))

    def setup_database(self):
        self.ui.database.setup(self.srv.database)
        self.ui.dbroot_button.setDefaultAction(self.ui.dbroot)
        self.ui.db_list = []
        self.database_mapper = QSignalMapper(self)
        self.database_mapper.mapped.connect(self.on_db_triggered)
        self.srv.database.current.changed.connect(self.update_database)

    def setup_playlists(self):
        self.ui.playlists.setup(self.srv.playlists)
        self.ui.plroot_button.setDefaultAction(self.ui.plroot)
        self.ui.pl_button.hide()
        self.ui.pl_button.setDefaultAction(self.ui.pl)
        self.srv.playlists.current.changed.connect(self.update_playlists)

    def setup_search(self):
        self.ui.search_results.setup(self.srv.search)
        self.ui.search_button.setDefaultAction(self.ui.search)

    @property
    def current_view(self):
        i = self.ui.tabs.currentIndex()
        if i == 0: return self.ui.database
        elif i == 1: return self.ui.playlists
        elif i == 2: return self.ui.search_results

    def closeEvent(self, e):
        self.main.settings['gui']['browser_geometry'] = str(self.saveGeometry().toBase64())
        self.main.settings['gui']['browser_tab'] = str(self.ui.tabs.currentIndex())
        super().closeEvent(e)

    def contextMenuEvent(self, e):
        e.accept()
        self.ui.add.setVisible(self.current_view.can_add_to_queue())
        self.ui.remove.setVisible(self.current_view.can_remove())
        self.ui.rename.setVisible(self.current_view.can_rename())
        self.ui.details.setVisible(self.current_view.details() is not None)
        self.ui.context_menu.popup(e.globalPos())

    def on_state_changed(self, state):
        c = state != 'disconnect'
        for act in ('dbroot', 'plroot', 'pl', 'search', 'add', 'addplay',
                'replace', 'replaceplay', 'remove', 'rename', 'details'):
            getattr(self.ui, act).setEnabled(c)
        for b in self.ui.db_list:
            b.defaultAction().setEnabled(c)
        self.ui.what.setEnabled(c)
        self.ui.query.setEnabled(c)

    def update_database(self, path):
        p = path.split('/')
        if p == ['']:
            p = []
        for i in range(len(self.ui.db_list), len(p)):
            a = QAction(self)
            a.triggered.connect(self.database_mapper.map)
            self.database_mapper.setMapping(a, i)
            b = QToolButton(self)
            b.setDefaultAction(a)
            b.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred))
            self.ui.db_layout.insertWidget(i+1, b)
            self.ui.db_list.append(b)
        for i in range(len(p)):
            self.ui.db_list[i].defaultAction().setText(p[i])
            self.ui.db_list[i].show()
        for i in range(len(p), len(self.ui.db_list)):
            self.ui.db_list[i].hide()

    def update_playlists(self, name):
        if name == '':
            self.ui.pl_button.hide()
        else:
            self.ui.pl_button.defaultAction().setText(name)
            self.ui.pl_button.show()

    @Slot()
    def on_close_triggered(self):
        self.close()

    @Slot()
    def on_dbroot_triggered(self):
        self.srv.database.cd('')

    def on_db_triggered(self, number):
        path = '/'.join(self.srv.database.current.value.split('/')[:number+1])
        self.srv.database.cd(path)

    @Slot()
    def on_plroot_triggered(self):
        self.srv.playlists.cd('')

    @Slot()
    def on_pl_triggered(self):
        self.srv.playlists.refresh()

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
    def on_details_triggered(self):
        d = self.current_view.details()
        if d is not None:
            self.main.info.exec_('details', d, 'Details')

