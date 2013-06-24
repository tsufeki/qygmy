
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
        if 0 <= e.x() < sz.width() and 0 <= e.y() < sz.height():
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

    def setup(self, model):
        self.setModel(model)
        self.delegate = RichTextDelegate()
        self.setItemDelegate(self.delegate)

        h = self.header()
        h.setResizeMode(0, QHeaderView.Stretch)
        for i in range(1,h.count()):
            h.setResizeMode(i, QHeaderView.ResizeToContents)

        self.doubleClicked.connect(self._double_clicked)

    def selectionChanged(self, selected, deselected):
        self.selection_changed.emit()
        super().selectionChanged(selected, deselected)

    def selection(self):
        return sorted(i.row()
                for i in self.selectedIndexes()
                if i.column() == 0)

    def _double_clicked(self, index):
        self.model().double_clicked(index.row())

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

    def set_priority(self, prio):
        self.model().set_priority(self.selection(), prio)

