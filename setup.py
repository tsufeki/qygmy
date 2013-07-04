#!/usr/bin/env python3

import os
import glob
import shutil
from distutils.core import setup
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.command.sdist import sdist
from distutils.spawn import spawn

from qygmy.__version__ import version, version_info
SRC_DIR = os.path.dirname(os.path.abspath(__file__))


class build(build):
    def run(self):
        os.chdir(SRC_DIR)
        spawn(['make'])
        super().run()

class clean(clean):
    def run(self):
        os.chdir(SRC_DIR)
        spawn(['make', 'clean'])
        super().run()

class deb(sdist):
    def run(self):
        spawn(['make', 'dchrelease'])
        self.dist_dir = os.path.join(self.dist_dir, 'deb')
        super().run()
        name = self.distribution.get_name()
        version = self.distribution.get_version()
        ext = 'tar.gz'
        sourcedir = name + '-' + version
        tar = sourcedir + '.' + ext
        debversion = version.replace('.dev', '~dev')
        origtar = name + '_' + debversion + '.orig.' + ext
        os.chdir(self.dist_dir)
        spawn(['tar', 'xvzf', tar])
        os.rename(tar, origtar)
        os.chdir(sourcedir)
        spawn(['debuild'])
        os.chdir('..')
        shutil.rmtree(sourcedir, True)
        for i in glob.glob(name + '_' + debversion + '-*.build'):
            os.remove(i)


setup(
    name = 'qygmy',
    version = version,
    description = "Simple graphical MPD client.",
    long_description = """Simple graphical MPD client written in Python and Qt/PySide. It's interface
is strongly inspired by Pygmy (the GTK client).""",
    author = 'tsufeki',
    author_email = 'tsufeki@ymail.com',
    url = 'https://github.com/tsufeki/qygmy',
    download_url = 'https://github.com/tsufeki/qygmy/archive/v{}.tar.gz'.format(version),
    license = 'BSD',
    install_requires = [
        'PySide>=1.1.2',
        'python-mpd2',
    ],
    packages = [
        'qygmy',
        'qygmy.templates',
        'qygmy.ui',
    ],
    package_data = {
        'qygmy': ['translations/*.qm', 'gittimestamp.txt'],
    },
    scripts = ['bin/qygmyrun'],
    data_files = [
        ('share/applications', ['qygmy.desktop']),
        ('share/man/man1', ['qygmy.1']),
    ],
    classifiers = [
        {
            'alpha': 'Development Status :: 3 - Alpha',
            'beta':  'Development Status :: 4 - Beta',
            'rc':    'Development Status :: 4 - Beta',
            'final': 'Development Status :: 5 - Production/Stable',
        }[version_info[3]],
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Topic :: Multimedia :: Sound/Audio',
    ],
    cmdclass = {
        'clean': clean,
        'build': build,
        'deb': deb,
    },
)
