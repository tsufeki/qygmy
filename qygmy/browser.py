
from PySide.QtCore import *
from PySide.QtGui import *

from .uiutils import RichTextDelegate
from .ui.browser import Ui_browser


class Browser(QMainWindow):
    def __init__(self, main, formatter):
        super().__init__()
        self.main = main
        self.p = main.p
        self.fmt = formatter
        self.setup_ui()
        self.p.database_cwd.update(None, force=True)
        self.p.stored_playlists_cwd.update(None, force=True)

    def setup_ui(self):
        self.ui = Ui_browser()
        self.ui.setupUi(self)
        self.setup_database()
        self.setup_stored_playlists()
        self.setup_search()
        self.ui.action_add.setIcon(QIcon.fromTheme('list-add'))
        self.ui.action_remove.setIcon(QIcon.fromTheme('list-remove'))
        self.setWindowIcon(QIcon.fromTheme('list-add'))
        self.ui.action_close.setIcon(QIcon.fromTheme('window-close'))
        self.ui.close.setDefaultAction(self.ui.action_close)
        self.ui.tabs.setCornerWidget(self.ui.close)

        cm = QMenu(self)
        cm.addAction(self.ui.action_add)
        cm.addAction(self.ui.action_addplay)
        cm.addAction(self.ui.action_remove)
        cm.addAction(self.ui.action_details)
        cm.addAction(self.ui.action_close)
        self.ui.context_menu = cm

        self.p.state.changed.connect(self.on_state_changed)

    def setup_database(self):
        self.ui.db_delegate = RichTextDelegate()
        self.ui.database.setModel(self.p.database)
        self.ui.database.setItemDelegate(self.ui.db_delegate)

        h = self.ui.database.header()
        h.setResizeMode(0, QHeaderView.Stretch)
        for i in range(1,h.count()):
            h.setResizeMode(i, QHeaderView.ResizeToContents)

        self.ui.tabs.setTabIcon(0, QIcon.fromTheme('folder-sound'))
        self.ui.action_db_root.setIcon(QIcon.fromTheme('folder-sound'))
        self.ui.db_root_crumb.setDefaultAction(self.ui.action_db_root)
        self.ui.db_crumbs = []
        self.db_mapper = QSignalMapper(self)
        self.db_mapper.mapped.connect(self.on_db_crumb_triggered)
        self.p.database_cwd.changed.connect(self.update_db_crumbs)

    def setup_stored_playlists(self):
        self.ui.pl_delegate = RichTextDelegate()
        self.ui.playlists.setModel(self.p.stored_playlists)
        self.ui.playlists.setItemDelegate(self.ui.pl_delegate)

        h = self.ui.playlists.header()
        h.setResizeMode(0, QHeaderView.Stretch)
        for i in range(1,h.count()):
            h.setResizeMode(i, QHeaderView.ResizeToContents)

        self.ui.tabs.setTabIcon(1, QIcon.fromTheme('document-multiple'))
        self.ui.action_pl_root.setIcon(QIcon.fromTheme('document-multiple'))
        self.ui.pl_root_crumb.setDefaultAction(self.ui.action_pl_root)
        self.ui.pl_crumb0.hide()
        self.ui.pl_crumb0.setDefaultAction(self.ui.action_pl_crumb0)
        self.p.stored_playlists_cwd.changed.connect(self.update_pl_crumbs)

    def setup_search(self):
        self.ui.se_delegate = RichTextDelegate()
        self.ui.search_results.setModel(self.p.search_results)
        self.ui.search_results.setItemDelegate(self.ui.se_delegate)

        h = self.ui.search_results.header()
        h.setResizeMode(0, QHeaderView.Stretch)
        for i in range(1,h.count()):
            h.setResizeMode(i, QHeaderView.ResizeToContents)

        self.ui.tabs.setTabIcon(2, QIcon.fromTheme('edit-find'))
        self.ui.action_search.setIcon(QIcon.fromTheme('edit-find'))
        self.ui.search.setDefaultAction(self.ui.action_search)

    def contextMenuEvent(self, e):
        e.accept()
        if self.ui.tabs.currentIndex() == 0:
            wdgt = self.ui.database
        elif self.ui.tabs.currentIndex() == 1:
            wdgt = self.ui.playlists
        else:
            wdgt = self.ui.search_results
        ind = [i.row() for i in wdgt.selectedIndexes() if i.column() == 0]
        self.ui.action_details.setVisible(len(ind) == 1 and 'file' in wdgt.model().songs[ind[0]])
        self.ui.action_remove.setVisible(self.ui.tabs.currentIndex() == 1)
        self.ui.context_menu.popup(e.globalPos())

    def on_state_changed(self, state):
        c = state != 'disconnect'
        for act in ('add', 'addplay', 'db_root', 'pl_root', 'search', 'remove',
                'pl_crumb0'):
            getattr(self.ui, 'action_' + act).setEnabled(c)
        for b in self.ui.db_crumbs:
            b.defaultAction().setEnabled(c)
        self.ui.what.setEnabled(c)
        self.ui.query.setEnabled(c)

    @Slot(str)
    def update_db_crumbs(self, path):
        p = path.split('/')
        if p == ['']:
            p = []
        for i in range(len(self.ui.db_crumbs), len(p)):
            a = QAction(self)
            a.triggered.connect(self.db_mapper.map)
            self.db_mapper.setMapping(a, i)
            b = QToolButton(self)
            b.setDefaultAction(a)
            b.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred))
            self.ui.db_crumbs_lo.insertWidget(i+1, b)
            self.ui.db_crumbs.append(b)
        for i in range(len(p)):
            self.ui.db_crumbs[i].defaultAction().setText(p[i])
            self.ui.db_crumbs[i].show()
        for i in range(len(p), len(self.ui.db_crumbs)):
            self.ui.db_crumbs[i].hide()

    @Slot(str)
    def update_pl_crumbs(self, name):
        if name == '':
            self.ui.pl_crumb0.hide()
        else:
            self.ui.pl_crumb0.defaultAction().setText(name)
            self.ui.pl_crumb0.show()

    @Slot()
    def on_action_close_triggered(self):
        self.hide()

    @Slot()
    def on_action_db_root_triggered(self):
        self.p.database_cwd.update('', force=True)

    def on_db_crumb_triggered(self, number):
        path = '/'.join(self.p.database_cwd.value.split('/')[:number+1])
        self.p.database_cwd.update(path, force=True)

    @Slot(QModelIndex)
    def on_database_doubleClicked(self, index):
        self.p.database_add_or_cd(index.row())

    @Slot()
    def on_action_pl_root_triggered(self):
        self.p.stored_playlists_cwd.update('', force=True)

    @Slot()
    def on_action_pl_crumb0_triggered(self):
        self.p.stored_playlists_cwd.update(self.p.stored_playlists_cwd.value, force=True)

    @Slot(QModelIndex)
    def on_playlists_doubleClicked(self, index):
        self.p.playlists_add_or_cd(index.row())

    @Slot()
    def on_action_search_triggered(self):
        self.p.search_query.update((self.ui.what.currentIndex(), self.ui.query.text()), force=True)

    @Slot(QModelIndex)
    def on_search_results_doubleClicked(self, index):
        self.p.search_add([index.row()])

    @Slot()
    def on_action_add_triggered(self, play=False):
        if self.ui.tabs.currentIndex() == 0:
            ind, fun = self.ui.database.selectedIndexes(), self.p.database_add
        elif self.ui.tabs.currentIndex() == 1:
            ind, fun = self.ui.playlists.selectedIndexes(), self.p.playlists_add
        elif self.ui.tabs.currentIndex() == 2:
            ind, fun = self.ui.search_results.selectedIndexes(), self.p.search_add
        positions = [i.row() for i in ind if i.column() == 0]
        fun(positions, play)

    @Slot()
    def on_action_addplay_triggered(self):
        self.on_action_add_triggered(True)

    @Slot()
    def on_action_remove_triggered(self):
        if self.ui.tabs.currentIndex() == 1:
            self.p.playlists_remove([i.row()
                for i in self.ui.playlists.selectedIndexes()
                if i.column() == 0
            ])

    @Slot()
    def on_action_details_triggered(self):
        if self.ui.tabs.currentIndex() == 0:
            wdgt = self.ui.database
        elif self.ui.tabs.currentIndex() == 1:
            wdgt = self.ui.playlists
        else:
            wdgt = self.ui.search_results
        ind = [i.row() for i in wdgt.selectedIndexes() if i.column() == 0]
        if len(ind) == 1:
            s = wdgt.model().songs[ind[0]]
            if 'file' in s:
                self.main.details.show_details(s)

