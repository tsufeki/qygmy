#!/usr/bin/env python3

import os
import glob
import shutil
import re
from distutils.core import setup
from distutils.cmd import Command
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.command.sdist import sdist
from distutils import archive_util

from qygmy.__version__ import version, version_info
SRC_DIR = os.path.dirname(os.path.abspath(__file__))


class build(build):

    def run(self):
        oldcwd = os.getcwd()
        os.chdir(SRC_DIR)
        self.spawn(['make'])
        super().run()
        os.chdir(oldcwd)


class clean(clean):

    def run(self):
        oldcwd = os.getcwd()
        os.chdir(SRC_DIR)
        self.spawn(['make', 'clean'])
        super().run()
        os.chdir(oldcwd)


class sdist(sdist):

    def finalize_options(self):
        archive_util.ARCHIVE_FORMATS['xztar'] = (None, [], "xz'd tar-file")
        super().finalize_options()
        del archive_util.ARCHIVE_FORMATS['xztar']

    def make_archive(self, base_name, format, root_dir=None, base_dir=None):
        if format != 'xztar':
            return super().make_archive(base_name, format, root_dir, base_dir)
        tar = super().make_archive(base_name, 'tar', root_dir, base_dir)
        xz_opts = '-zf'
        self.spawn(['xz', xz_opts, tar])
        return tar + '.xz'


class bdist_deb(Command):

    description = "create a Debian binary package"

    user_options = [
        ('dist-dir=', 'd', "directory to put final Debian package files in"),
    ]

    def initialize_options(self):
        self.dist_dir = None

    def finalize_options(self):
        self.set_undefined_options('bdist', ('dist_dir', 'dist_dir'))
        self.dist_dir = os.path.abspath(self.dist_dir)

    def run(self):
        saved_dist_files = self.distribution.dist_files[:]
        oldcwd = os.getcwd()
        os.chdir(SRC_DIR)
        sdist_cmd = self.reinitialize_command('sdist')
        sdist_cmd.formats = ['xztar']
        sdist_cmd.dist_dir = self.dist_dir
        sdist_cmd.ensure_finalized()

        self.spawn(['make', 'dchrelease'])
        sdist_cmd.run()
        self.distribution.dist_files = saved_dist_files

        name = self.distribution.get_name()
        version = self.distribution.get_version()
        ext = 'tar.xz'
        sourcedir = name + '-' + version
        tar = sourcedir + '.' + ext
        debversion = re.sub(r'([a-c])', r'~\1', version.replace('.dev', '~dev'))
        origtar = name + '_' + debversion + '.orig.' + ext

        os.chdir(self.dist_dir)
        self.spawn(['tar', 'xvf', tar])
        if not self.dry_run:
            os.rename(tar, origtar)
            os.chdir(sourcedir)
        self.spawn(['debuild'])
        if not self.dry_run:
            os.chdir(self.dist_dir)
            shutil.rmtree(sourcedir, True)
            for i in glob.glob(name + '_' + debversion + '-*.build'):
                os.remove(i)
        deb = sorted(glob.glob(name + '_' + debversion + '-*_all.deb'))[-1]
        debfull = os.path.abspath(os.path.join(self.dist_dir, deb))
        self.distribution.dist_files.append(('bdist_dumb', 'any', debfull))
        os.chdir(oldcwd)


setup(
    name = 'qygmy',
    version = version,
    description = "Simple graphical MPD client.",
    long_description = """Simple graphical MPD client written in Python and Qt/PySide. It's interface
is strongly inspired by Pygmy (the GTK client). Qygmy's most remarkable
feature is its powerful template engine, allowing highly customizable display.""",
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
        'sdist': sdist,
        'bdist_deb': bdist_deb,
    },
)
