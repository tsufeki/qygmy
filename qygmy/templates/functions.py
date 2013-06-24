
import re


def lazy_noop(*args): return ''


# Conditionals

def lazy_if(cond, yes, no): return yes() if cond() else no()

def lazy_if2(*args):
    for a in args:
        val = a()
        if val:
            return val
    return ''

def lazy_if3(*args):
    if len(args) == 0:
        return ''
    if len(args) == 1:
        return args[0]()
    return lazy_if(args[0], args[1], lambda: lazy_if3(*args[2:]))


# String operations

def f_lower(text): return text.lower()
def f_upper(text): return text.upper()
def f_left(text, num): return text[:int(num)]
def f_right(text, num): return text[-int(num):]
def f_num(num, length): return '{{:0{}d}}'.format(int(length)).format(int(num))
def f_replace(text, search, replace): return text.replace(search, replace)
def f_in(x, y): return '1' if x in y else ''
def f_trim(text, chars=None): return text.strip(chars)
def f_len(text): return str(len(text))

def f_eq(x, y): return '1' if x == y else ''
def f_ne(x, y): return '1' if x != y else ''


# Regular expressions

def f_rsearch(text, pattern):
    m = re.search(pattern, text)
    if m is None:
        return ''
    if m.lastindex is None:
        return m.group(0)
    return m.group(1)

def f_rreplace(text, pattern, replace):
    return re.sub(pattern, replace, text)


# Integer arithmetic

def f_add(*args): return str(sum(int(i) for i in args))
def f_sub(x, y): return str(int(x) - int(y))
def f_div(x, y): return str(int(x) // int(y))
def f_mod(x, y): return str(int(x) % int(y))

def f_mul(*args):
    r = 1
    for i in args:
        r *= int(i)
    return str(r)

def f_lt(x, y): return '1' if int(x) < int(y) else ''
def f_lte(x, y): return '1' if int(x) <= int(y) else ''
def f_gt(x, y): return '1' if int(x) > int(y) else ''
def f_gte(x, y): return '1' if int(x) >= int(y) else ''


# Boolean

def lazy_or(x, y): return str(x() or y())
def lazy_and(x, y): return str(x() and y())
def f_not(x): return '' if x else '1'


# Context operations

def context_get(ctx, name, default=''):
    if name in ctx and ctx[name]:
        return ctx[name]
    else:
        return default

def context_set(ctx, name, value):
    ctx[name] = value
    return ''

def context_unset(ctx, name):
    if name in ctx:
        del ctx[name]
    return ''

# Other

def f_time(seconds):
    if seconds == '':
        return ''
    t = int(seconds)
    sign = ''
    if t < 0:
        sign = '-'
        t = -t
    t, s = divmod(t, 60)
    t, m = divmod(t, 60)
    d, h = divmod(t, 24)

    if d != 0:
        return '{}{}d {:02d}:{:02d}:{:02d}'.format(sign, d, h, m, s)
    elif h != 0:
        return '{}{}:{:02d}:{:02d}'.format(sign, h, m, s)
    else:
        return '{}{:02d}:{:02d}'.format(sign, m, s)

