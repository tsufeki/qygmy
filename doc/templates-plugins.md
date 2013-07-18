Template functions plugins
==========================

You can add additional functions to be used in templates. Such plugin is
a regular python module named `tmplplugin_<plugin name>.py` and placed in
the `$XDG_CONFIG_HOME/qygmy/` directory (which usually means `~/.config/qygmy/`.

Python function's name prefix determines how it will be called.

- `f_<name>` functions are called straightforwardly with only `str` arguments.
- `lazy_<name>` means all arguments will be zero-argument, `str`-returning
    lambdas, to be called when needed.
- `context_<name>` function's first argument will be a `dict` with all defined
    variables.
- `lazycontext_<name>` is the mix of the two above. Context argument won't be
    lazy.

All functions must return a `str` no matter what.

Examples
--------

```.py
def f_cat(x,y):
    return x + ' ' + y

def lazy_myif(cond, yes, no=lambda:''):
    return yes() if cond() else no()

def context_myget(ctx, name, default=''):
    return ctx.get(name, default)

def lazycontext_ifdef(ctx, name, yes, no):
    if name() in ctx and ctx[name()]:
        return yes()
    return no()
```

```.txt
$cat(aaa,bbb) -> aaa bbb
$myif(1,aaa,$nonexistingfunction(bbb)) -> aaa
$myget(title) -> Yellow Submarine
$myget(nonexistingvar,aaa) -> aaa
```

