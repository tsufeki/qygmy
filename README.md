Qygmy
=====

Qygmy is a simple MPD client written is Python 3 and Qt/PySide.

Requirements
------------

* Python >= 3.3
* PySide >= 1.1.2
* [python-mpd2][1]

  [1]: https://github.com/Mic92/python-mpd2

Installation
------------

* Using `pip`:

        pip install qygmy

* On Debian: first, install `python3-mpd2` as in [this guide][2]. Then download
  the `.deb` file from [here][3] and install it:

        dpkg -i qygmy_*_all.deb

  `.deb`s can be build from source using:

        python3 ./setup.py deb

  [2]: https://github.com/Mic92/python-mpd2/blob/master/INSTALL.rst#debian
  [3]: https://pypi.python.org/pypi/qygmy
