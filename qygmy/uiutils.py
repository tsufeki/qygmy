
from PySide.QtCore import *
from PySide.QtGui import *


class RichTextDelegate(QStyledItemDelegate):
    def _make_document(self, text):
        doc = QTextDocument()
        doc.setHtml(text)
        doc.setDocumentMargin(3)
        return doc

    def paint(self, painter, option, index):
        option = QStyleOptionViewItemV4(option)
        self.initStyleOption(option, index)
        style = QApplication.style() if option.widget is None else option.widget.style()
        doc = self._make_document(option.text)
        option.text = ''
        style.drawControl(QStyle.CE_ItemViewItem, option, painter)
        ctx = QAbstractTextDocumentLayout.PaintContext()
        if option.state & QStyle.State_Selected:
            ctx.palette.setColor(QPalette.Text, option.palette.color(QPalette.Active, QPalette.HighlightedText))
        textRect = style.subElementRect(QStyle.SE_ItemViewItemText, option)
        painter.save()
        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        doc.documentLayout().draw(painter, ctx)
        painter.restore()

    def sizeHint(self, option, index):
        option = QStyleOptionViewItemV4(option);
        self.initStyleOption(option, index);
        doc = self._make_document(option.text);
        return QSize(doc.size().width(), doc.size().height())


class ClickableProgressBar(QProgressBar):
    def mousePressEvent(self, e):
        sz = self.size()
        if e.button() == Qt.LeftButton and 0 <= e.x() < sz.width() and 0 <= e.y() < sz.height():
            e.accept()
            minv, maxv = self.minimum(), self.maximum()
            newvalue = minv + round((e.x() / sz.width()) * (maxv - minv))
            self.clicked.emit(newvalue)
        else:
            e.ignore()

    clicked = Signal(int)


class ChangeDuringDragTabBar(QTabBar):
    def __init__(self, parent=None, drag_change_interval=1000):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._dragtimer = QTimer(self)
        self._dragtimer.setInterval(drag_change_interval)
        self._dragtimer.setSingleShot(True)
        self._dragtab = -1
        self._dragtimer.timeout.connect(self._change_tab)

    def _change_tab(self):
        if self._dragtab >= 0:
            self.setCurrentIndex(self._dragtab)

    def dropEvent(self, e):
        self._dragtimer.stop()
        self._dragtab = -1
        super().dropEvent(e)

    def dragLeaveEvent(self, e):
        self._dragtimer.stop()
        self._dragtab = -1
        super().dragLeaveEvent(e)

    def dragEnterEvent(self, e):
        self._dragtimer.stop()
        self._dragtab = self.tabAt(e.pos())
        if self._dragtab >= 0:
            self._dragtimer.start()
        e.accept()
        super().dragEnterEvent(e)

    def dragMoveEvent(self, e):
        t = self.tabAt(e.pos())
        if t != self._dragtab:
            self._dragtimer.stop()
            self._dragtab = t
            if t >= 0:
                self._dragtimer.start()
        super().dragMoveEvent(e)


class ChangeDuringDragTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._tabbar = ChangeDuringDragTabBar(self)
        self.setTabBar(self._tabbar)


class SonglistView(QTreeView):

    selection_changed = Signal()

    def __init__(self, parent):
        super().__init__(parent)
        self._enter_action = QAction('Add or descend into', self)
        self._enter_action.setShortcut(QKeySequence(self.tr('Return')))
        self._enter_action.setShortcutContext(Qt.WidgetWithChildrenShortcut)
        self.addAction(self._enter_action)

    def setup(self, model):
        self.setModel(model)
        self._delegate = RichTextDelegate()
        self.setItemDelegate(self._delegate)

        h = self.header()
        h.setResizeMode(0, QHeaderView.Stretch)
        for i in range(1,h.count()):
            h.setResizeMode(i, QHeaderView.ResizeToContents)

        self.doubleClicked.connect(self._double_clicked)
        self._enter_action.triggered.connect(self._enter_pressed)

    def selectionChanged(self, selected, deselected):
        self.selection_changed.emit()
        super().selectionChanged(selected, deselected)

    def selection(self):
        return sorted(i.row()
                for i in self.selectedIndexes()
                if i.column() == 0)

    def _double_clicked(self, index):
        self.model().item_chosen(index.row())

    def _enter_pressed(self):
        if self.state() == self.EditingState:
            index = self.currentIndex()
            editor = self.indexWidget(index)
            if editor:
                self.commitData(editor)
                self.closeEditor(editor, QAbstractItemDelegate.NoHint)
        else:
            s = self.selection()
            if len(s) == 1:
                self.model().item_chosen(s[0])
            elif len(s) > 0 and self.model().can_add_to_queue(s):
                self.model().add_to_queue(s)

    def details(self):
        return self.model().details(self.selection())

    def can_add_to_queue(self):
        return self.model().can_add_to_queue(self.selection())

    def can_remove(self):
        return self.model().can_remove(self.selection())

    def can_rename(self):
        return self.model().can_rename(self.selection())

    def can_set_priority(self, prio):
        return self.model().can_set_priority(self.selection(), prio)

    def add_selected_to_queue(self, play=False, replace=False):
        self.model().add_to_queue(self.selection(), play, replace)

    def remove_selected(self):
        self.model().remove(self.selection())

    def rename_selected(self):
        s = self.selection()
        if len(s) == 1 and self.can_rename():
            i = self.model().index(s[0], 0)
            self.setCurrentIndex(i)
            self.edit(i)

    def set_priority(self, prio):
        self.model().set_priority(self.selection(), prio)

class PathBar(QWidget):

    clicked = Signal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.path = []
        self._mapper = QSignalMapper(self)
        self._mapper.mapped.connect(self._clicked)
        self._label = QLabel(self)
        self._label.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred))
        self._layout = QHBoxLayout(self)
        self._layout.addWidget(self._label)
        self._layout.setContentsMargins(0, 4, 0, 0)
        self.buttons = []
        self.actions = []
        self.set_path('')

    def _make_button(self):
        number = len(self.buttons)
        a = QAction(self)
        a.triggered.connect(self._mapper.map)
        self._mapper.setMapping(a, number)
        b = QToolButton(self)
        b.setDefaultAction(a)
        b.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred))
        self._layout.insertWidget(number, b)
        self.actions.append(a)
        self.buttons.append(b)

    def set_root_icon(self, theme_name):
        self.actions[0].setIcon(QIcon.fromTheme(theme_name))

    def _clicked(self, number):
        self.clicked.emit('/'.join(self.path[:number]))

    def set_path(self, path):
        self.path = path.strip('/').split('/')
        if self.path == ['']:
            self.path = []
        for i in range(len(self.buttons), len(self.path) + 1):
            self._make_button()
        for i in range(1, len(self.path) + 1):
            self.actions[i].setText(self.path[i-1])
            self.buttons[i].show()
        for i in range(len(self.path) + 1, len(self.buttons)):
            self.buttons[i].hide()

