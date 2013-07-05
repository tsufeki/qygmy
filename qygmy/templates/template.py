#!/usr/bin/env python3

import re

from PySide.QtGui import QApplication

from . import functions


IDENTIFIER = r'([_a-zA-Z][_a-zA-Z0-9]*)'


class TemplateError(Exception):
    pass


class Renderable:
    def render(self, context):
        return ''


class Text(Renderable):
    def __init__(self, text):
        self.text = text

    def render(self, context):
        return self.text

    def __repr__(self):
        return repr(self.text)


class Element(Renderable):

    def __init__(self, tmpl, src, start, end):
        self.template = tmpl
        self.src = src
        self.start = start
        self.end = end

    @classmethod
    def parse_first(cls, tmpl, src, pos=0):
        return None

    def parse_rest(self):
        pass


class RegexElement(Element):

    regex = None

    @classmethod
    def parse_first(cls, tmpl, src, pos=0):
        m = cls.regex.search(src, pos)
        if m is None:
            return None
        return cls(tmpl, src, m.start(), m.end(), *m.groups())


class Backslash(RegexElement):

    regex = re.compile(r'\\(.)')

    def __init__(self, tmpl, src, start, end, char):
        super().__init__(tmpl, src, start, end)
        self.char = char

    def render(self, context):
        return self.char

    def __repr__(self):
        return 'Backslash({!r})'.format(self.char)


class Variable(RegexElement):

    regex = re.compile(r'%' + IDENTIFIER + r'%')

    def __init__(self, tmpl, src, start, end, name):
        super().__init__(tmpl, src, start, end)
        self.name = name.lower()

    def render(self, context):
        return str(context.get(self.name, ''))

    def __repr__(self):
        return 'Variable({!r})'.format(self.name)


class Sequence(Element):

    class End(RegexElement):
        regex = re.compile(r'$')

    def __init__(self, tmpl, src, start, end, delims=[], types=None):
        super().__init__(tmpl, src, start, end)
        if types is None:
            types = [Backslash, Variable, Function]
        self.delims = delims + [self.End]
        self.types = types + self.delims
        self.elems = []

    @classmethod
    def parse_first(cls, tmpl, src, pos=0, delims=[], types=None):
        return cls(tmpl, src, pos, pos, delims, types)

    def parse_rest(self):
        while True:
            matches = [t.parse_first(self.template, self.src, self.end) for t in self.types]
            minimum = None
            for m in matches:
                if m is not None and (minimum is None or m.start < minimum.start):
                    minimum = m
            if self.end < minimum.start:
                self.elems.append(Text(self.src[self.end:minimum.start]))
            minimum.parse_rest()
            self.end = minimum.end
            if type(minimum) in self.delims:
                self.last = minimum
                return
            self.elems.append(minimum)

    def render(self, context):
        return ''.join(e.render(context) for e in self.elems)

    def __repr__(self):
        return '+'.join(repr(e) for e in self.elems)


class Function(RegexElement):

    regex = re.compile(r'\$' + IDENTIFIER + r'\(')


    class Comma(RegexElement):
        regex = re.compile(r',')


    class ClosingParen(RegexElement):
        regex = re.compile(r'\)')


    def __init__(self, tmpl, src, start, end, name):
        super().__init__(tmpl, src, start, end)
        self.name = name.lower()
        self.args = []

        self._ctx_additions = {
            '__timefmt__': (
                QApplication.translate('templates', '{}{}d {:02d}:{:02d}:{:02d}'),
                QApplication.translate('templates', '{}{}:{:02d}:{:02d}'),
                QApplication.translate('templates', '{}{:02d}:{:02d}'),
            ),
        }

        self.call = None
        for module in reversed(self.template.functions):
            f = getattr(module, 'lazycontext_' + self.name, None)
            if f is not None:
                self.function = f
                self.call = self.call_lazycontext
                return
            f = getattr(module, 'context_' + self.name, None)
            if f is not None:
                self.function = f
                self.call = self.call_context
                return
            f = getattr(module, 'lazy_' + self.name, None)
            if f is not None:
                self.function = f
                self.call = self.call_lazy
                return
            f = getattr(module, 'f_' + self.name, None)
            if f is not None:
                self.function = f
                self.call = self.call_f
                return

    def parse_rest(self):
        while True:
            seq = Sequence.parse_first(self.template, self.src, self.end,
                    delims=[self.Comma, self.ClosingParen])
            seq.parse_rest()
            self.end = seq.end
            self.args.append(seq)
            if type(seq.last) != self.Comma:
                return

    def call_f(self, context):
        args = [a.render(context) for a in self.args]
        return self.function(*args)

    def call_lazy(self, context):
        args = [(lambda a=a: a.render(context)) for a in self.args]
        return self.function(*args)

    def call_context(self, context):
        context.update(self._ctx_additions)
        args = [a.render(context) for a in self.args]
        return self.function(context, *args)

    def call_lazycontext(self, context):
        context.update(self._ctx_additions)
        args = [(lambda a=a: a.render(context)) for a in self.args]
        return self.function(context, *args)

    def render(self, context):
        if self.call is None:
            raise TemplateError("function '${}' is not defined".format(self.name))
        try:
            return self.call(context)
        except Exception as e:
            raise TemplateError(str(e)) from e

    def __repr__(self):
        s = 'Function('
        s += ','.join(repr(i) for i in [self.name] + self.args)
        return s + ')'


class Template:
    def __init__(self, source, function_modules=[]):
        self.functions = [functions] + function_modules
        self.compiled = Sequence.parse_first(self, source)
        self.compiled.parse_rest()

    def render(self, context):
        r = []
        for e in self.compiled.elems:
            try:
                r.append(e.render(context))
            except TemplateError as e:
                r.append('##error: {}##'.format(str(e)))
        return ''.join(r)

    def __repr__(self):
        return 'Template({!r})'.format(self.compiled)

