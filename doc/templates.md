Qygmy's templates heavily borrow from [MusicBrainz Picard's scripting language][1],
which in turn is inspired by Foobar2000.

[1]: http://musicbrainz.org/doc/MusicBrainz_Picard/Documentation/Scripting

Syntax consists of three main elements: text (copied as is), variables and
functions. Additionally, current song and playlist item templates allow HTML
([the subset supported by Qt][2]). Special characters (`%`, `$`, `(`, `)`, `,`
and `\ ` itself) have to be escaped with a backslash, e.g. `$if(%album%,%album% \(%date%\))`.

[2]: https://qt-project.org/doc/qt-4.8/richtext-html-subset.html


Variables
=========

Variable consists of a variable's name between two percent signs, e.g. `%title%`.
Unrecognized names are resolved to empty string. Names are case-insensitive.
All values are strings.

State and metadata variables listed below are available in all templates, with
the following exceptions:

1. Playlist item template does not support state variables.
2. Progress bar template additionally supports `%elapsed%` and `%total%` (in
seconds, see `$time()`).

State variables
---------------

- `%playing%`
- `%paused%`
- `%stopped%`
- `%connected%` (i.e. precise state is not yet known)
- `%disconnected%`

Exactly one of those is set to `1`.

Song metadata variables
-----------------------

- `%file%`, `%directory%`, `%playlist%`: one of those is set to the item's
    full path, depending on it's type.
- `%filename%`: file name part of the above.
- `%prio%`: current priority (0-255, only for current queue items).
- `%length%`: length of the song in seconds (see `$time()`).
- `%track%`, `%totaltracks%`, `%disc%`, `%totaldiscs%`
- `%lastmodified%`: last modification date.
- All tags recognized by MPD: `%title%`, `%artist%`, `%album%`, `%date%`,
    `%comment%`, `%composer%`, `%performer%`, etc.


Functions
=========

Function names are case-insensitive. Functions take and return only strings.
Non-existing function, bad format when an integer is needed, etc. are all
errors and results in `##error: xxxxx##` message. In boolean context, empty
string is interpreted as false and everything else as true. Canonical true
value is `1`.

String operations
-----------------

- `$upper(text)`: convert to upper case.
- `$lower(text)`: convert to lower case.
- `$left(text,num)`: the first `num` characters of `text`.
- `$right(text,num)`: the last `num` characters of `text`.
- `$num(num,length)`: the number `num` padded to `length` with zeros.
- `$replace(text,search,replace)`: replace occurrences of `search` with `replace`.
- `$in(x,y)`: true iff `x` is a substring of `y`.
- `$trim(text,chars)`: strip `chars` from the beginning and end of `text`.
    `chars` may be omitted, defaults to whitespace then.
- `$len(text)`: the length of `text`.

Regular expressions
-------------------

See [regular expressions syntax help][3].

[3]: http://docs.python.org/3/library/re.html#regular-expression-syntax

- `$rsearch(text,pattern)`: return the first matched group, or the entire match
    if it doesn't exist.
- `$rreplace(text,pattern,replace)`: regular expression replace.

Integer arithmetic
------------------

Arguments of those functions are converted to integers.

- `$add(x1,x2,...)`: `x1 + x2 + ...`
- `$sub(x,y)`: `x - y`
- `$mul(x1,x2,...)`: `x1 * x2 * ...`
- `$div(x,y)`: `x / y`, e.g. `$div(7,2)` is `3`.
- `$mod(x,y)`: `x % y`, remainder.
- `$min(x1,x2,...)`: the smallest of `x1`, `x2`, ...
- `$max(x1,x2,...)`: the largest of `x1`, `x2`, ...
- `$lt(x,y)`: `x < y`
- `$lte(x,y)`: `x <= y`
- `$gt(x,y)`: `x > y`
- `$gte(x,y)`: `x >= y`

`$time()`
---------

- `$time(seconds)`: format `seconds` as time, e.g. `$time(3678)` is `1:01:18`.

Conditionals
------------

- `$eq(x,y)`: true iff `x` and `y` are equal (as strings).
- `$ne(x,y)`: true iff `x` and `y` are not equal.
- `$not(x)`: true iff `x` is false.

Arguments in the following functions are evaluated only as needed:

- `$if(condition,if_true,if_false)`: return `if_true` if `condition` is true,
    `if_false` otherwise.
- `$if2(a1,a2,...)`: return the first non-empty argument.
- `$if3(cond1,val1,cond2,val2,...,val_else)`: return the first `val<i>` for
    which `cond<i>` is true, or `val_else` if all `cond<i>` are false.
- `$or(x,y)`: `x or y`
- `$and(x,y)`: `x and y`
- `$noop(...)`: do nothing, return empty string.

Operations on variables
-----------------------

- `$get(name,default)`: return the value of the variable `%name%`, or `default`
    if it's empty or non-existing.
- `$set(name,value)`: set `%name%` to `value`.
- `$unset(name)`: unset `%name%`.
