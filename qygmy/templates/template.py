#!/usr/bin/env python3

import inspect
import io
from abc import ABCMeta, abstractmethod
from PySide.QtGui import QApplication

if __package__:
    from . import functions
else:
    import functions


class TemplateError(Exception):
    pass


class Renderable(metaclass=ABCMeta):
    @abstractmethod
    def render(self, context):
        pass


class Text(Renderable):
    def __init__(self, text):
        self.text = text

    def render(self, context):
        return self.text

    def __repr__(self):
        return repr(self.text)


class Variable(Renderable):
    def __init__(self, name):
        self.name = name

    def render(self, context):
        return context.get(self.name, '')

    def __repr__(self):
        return 'Variable: %s' % self.name


class Block(Renderable):
    def __init__(self):
        self.elements = []

    def append(self, elem):
        self.elements.append(elem)

    def isempty(self):
        return len(self.elements) == 0

    def render(self, context):
        return ''.join(e.render(context) for e in self.elements)

    def __repr__(self):
        return '\n'.join(repr(e) for e in self.elements)


class BaseFunction(Renderable):
    def __init__(self, function, args):
        self.function = function
        self.args = args

    def get_arg(self, arg, context):
        return arg.render(context)

    def get_args(self, context):
        return [self.get_arg(a, context) for a in self.args]

    def render(self, context):
        return self.function(*self.get_args(context))

    def __repr__(self):
        return (self.__class__.__name__ + ': ' + self.function.__name__ + '(\n  ' +
                ',\n'.join(repr(a) for a in self.args).replace('\n', '\n  ') + '\n)')


class Function(BaseFunction):
    pass


class LazyFunction(BaseFunction):
    def get_arg(self, arg, context):
        return lambda s=super(): s.get_arg(arg, context)


class ContextFunction(BaseFunction):
    def get_args(self, context):
        return [context] + super().get_args(context)


class LazyContextFunction(ContextFunction, LazyFunction):
    pass


class FunctionRepo:
    def __init__(self, modules, parent=None):
        self.parent = parent
        self.data = {}
        for module in modules:
            for name in dir(module):
                function = getattr(module, name)
                if name.startswith('f_'):
                    cls = Function
                    name = name[2:]
                elif name.startswith('lazy_'):
                    cls = LazyFunction
                    name = name[5:]
                elif name.startswith('context_'):
                    cls = ContextFunction
                    name = name[8:]
                elif name.startswith('lazycontext_'):
                    cls = LazyContextFunction
                    name = name[12:]
                else:
                    continue
                min_args = 0
                max_args = 0
                try:
                    sig = inspect.signature(function)
                except ValueError:
                    raise TemplateError("Can't obtain signature for function '%s' from %r" % (name, module))
                for p in sig.parameters.values():
                    if (p.kind == inspect.Parameter.POSITIONAL_ONLY or
                            p.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD):
                        if max_args is not None:
                            max_args += 1
                        if p.default == inspect.Parameter.empty:
                            min_args += 1
                    elif p.kind == inspect.Parameter.VAR_POSITIONAL:
                        max_args = None
                    elif (p.kind == inspect.Parameter.KEYWORD_ONLY and
                            p.default == inspect.Parameter.empty):
                        raise TemplateError("Required keyword-only arguments are not allowed: "
                                "function '%s' from %r" % (name, module))
                if cls == ContextFunction or cls == LazyContextFunction:
                    if max_args is not None and max_args < 1:
                        raise TemplateError("Context function must accept at least one argument: "
                                "function '%s' from %r" % (name, module))
                    min_args -= max(min_args - 1, 0)
                    max_args -= 1
                self.data[name] = (function, cls, min_args, max_args)

    def get(self, name):
        data = self.data.get(name, None)
        if data is None:
            if self.parent is None:
                data = (None, None, None, None)
            else:
                data = self.parent.get(name)
        return data


std_function_repo = FunctionRepo([functions])


class Parser:

    VAR = '%'
    FUNC = '$'
    FUNC_START = '('
    FUNC_COMMA = ','
    FUNC_END = ')'
    ESC = '\\'

    def __init__(self, source, function_repo):
        self.source = source
        self._function_repo = function_repo
        self._pos = -1
        self._line = 1
        self._col = 0

    def _get(self):
        self._oldpos = self._pos
        self._oldcol = self._col
        self._oldline = self._line
        self._pos += 1
        self._col += 1
        if self._pos >= len(self.source):
            return None
        c = self.source[self._pos]
        if c == '\n':
            self._line += 1
            self._col = 0
        return c

    def _unget(self):
        assert self._pos >= 0
        self._pos = self._oldpos
        self._col = self._oldcol
        self._line = self._oldline

    def _parse_identifier(self):
        s = io.StringIO()
        while True:
            c = self._get()
            if 'a' <= c <= 'z' or 'A' <= c <= 'Z' or '0' <= c <= '9' or c == '_':
                s.write(c)
            elif c is None:
                return s.getvalue()
            else:
                self._unget()
                return s.getvalue()

    def _parse_text(self, as_argument=False):
        s = io.StringIO()
        while True:
            c = self._get()
            if c is None:
                return Text(s.getvalue())
            elif c == self.VAR or c == self.FUNC or (
                    as_argument and (c == self.FUNC_COMMA or c == self.FUNC_END)):
                self._unget()
                return Text(s.getvalue())
            elif c == self.ESC:
                c = self._get()
                if c is not None:
                    s.write(c)
            else:
                s.write(c)

    def _parse_var(self):
        name = self._parse_identifier()
        if name == '':
            raise self._error('Syntax error: empty variable name')
        c = self._get()
        if c != self.VAR:
            raise self._error('Syntax error: undelimited variable')
        return Variable(name)

    def _parse_block(self, as_argument=False):
        elems = Block()
        while True:
            c = self._get()
            if c is None:
                return elems
            elif c == self.VAR:
                elems.append(self._parse_var())
            elif c == self.FUNC:
                elems.append(self._parse_func())
            elif as_argument and (c == self.FUNC_COMMA or c == self.FUNC_END):
                self._unget()
                return elems
            else:
                self._unget()
                elems.append(self._parse_text(as_argument))

    def _parse_func(self):
        name = self._parse_identifier()
        if name == '':
            raise self._error('Syntax error: empty function name')
        c = self._get()
        if c != self.FUNC_START:
            raise self._error("Syntax error: expected '('")
        args = []
        while True:
            args.append(self._parse_block(True))
            c = self._get()
            if c == self.FUNC_END:
                break
            elif c != self.FUNC_COMMA:
                raise self._error("Syntax error: expected ',' or ')'")
        if len(args) == 1 and args[0].isempty():
            args = []
        f, NodeClass, min_args, max_args = self._function_repo.get(name)
        if f is None:
            raise self._error("Unknown function: '%s'" % name)
        if len(args) < min_args:
            raise self._error("Function '%s' expects at least %d arguments, "
                    "%d given" % (name, min_args, len(args)))
        if max_args is not None and len(args) > max_args:
            raise self._error("Function '%s' expects at most %d arguments, "
                    "%d given" % (name, max_args, len(args)))
        return NodeClass(f, args)

    def parse(self):
        return self._parse_block()

    def _error(self, msg):
        return TemplateError(msg)

class Template(Renderable):
    std_vars = {
        '__timefmt__': (
            QApplication.translate('templates', '{}{}d {:02d}:{:02d}:{:02d}'),
            QApplication.translate('templates', '{}{}:{:02d}:{:02d}'),
            QApplication.translate('templates', '{}{:02d}:{:02d}'),
        ),
    }

    def __init__(self, source, function_modules=[]):
        if len(function_modules) > 0:
            repo = FunctionRepo(function_modules, std_function_repo)
        else:
            repo = std_function_repo
        self._block = Parser(source, repo).parse()

    def render(self, context):
        for k, v in self.std_vars.items():
            context.setdefault(k, v)
        return self._block.render(context)

    def __repr__(self):
        return repr(self._block)

if __name__ == '__main__':
    import sys
    t = Template(sys.argv[1])
    print(repr(t))
    if len(sys.argv) >= 3:
        print(repr(t.render(eval(sys.argv[2]))))

