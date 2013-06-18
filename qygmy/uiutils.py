
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

