
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
        #doc.setTextWidth(option.rect.width());
        return QSize(min(doc.size().width(), 800), doc.size().height())


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


class SonglistView(QTreeView):
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

    def add_selected_to_queue(self, play=False, replace=False):
        self.model().add_to_queue(self.selection(), play, replace)

    def remove_selected(self):
        self.model().remove(self.selection())

