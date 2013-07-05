#!/usr/bin/env python3

import os
import glob
import shutil
from distutils.core import setup
from distutils.cmd import Command
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.command.sdist import sdist

from qygmy.__version__ import version, version_info
SRC_DIR = os.path.dirname(os.path.abspath(__file__))


class build(build):

    def run(self):
        if not self.dry_run:
            os.chdir(SRC_DIR)
        self.spawn(['make'])
        super().run()


class clean(clean):

    def run(self):
        if not self.dry_run:
            os.chdir(SRC_DIR)
        self.spawn(['make', 'clean'])
        super().run()


class sdist(sdist):

    def finalize_options(self):
        self.ensure_string_list('formats')
        if self.formats is None or self.manifest_only:
            self.make_xztar = False
        else:
            self.make_tar = 'tar' in self.formats
            self.make_xztar = 'xztar' in self.formats
        if self.make_xztar:
            self.formats.remove('xztar')
            if not self.make_tar:
                self.formats.append('tar')
        super().finalize_options()

    def run(self):
        super().run()
        if self.make_xztar:
            name = self.distribution.get_name()
            version = self.distribution.get_version()
            tar = os.path.join(self.dist_dir, name + '-' + version + '.tar')
            if os.path.isfile(tar):
                xz_opts = '-zf'
                if self.make_tar:
                    xz_opts += 'k' # keep .tar
                self.spawn(['xz', xz_opts, tar])


class bdist_deb(Command):

    description = "create a Debian binary package"

    user_options = [
        ('dist-dir=', 'd', "directory to put final Debian package files in"),
    ]

    def initialize_options(self):
        self.dist_dir = None

    def finalize_options(self):
        self.set_undefined_options('bdist', ('dist_dir', 'dist_dir'))

    def run(self):
        sdist_cmd = self.reinitialize_command('sdist')
        sdist_cmd.formats = ['xztar']
        sdist_cmd.dist_dir = self.dist_dir
        sdist_cmd.ensure_finalized()

        self.spawn(['make', 'dchrelease'])
        sdist_cmd.run()

        name = self.distribution.get_name()
        version = self.distribution.get_version()
        ext = 'tar.xz'
        sourcedir = name + '-' + version
        tar = sourcedir + '.' + ext
        debversion = version.replace('.dev', '~dev')
        origtar = name + '_' + debversion + '.orig.' + ext

        if not self.dry_run:
            os.chdir(self.dist_dir)
        self.spawn(['tar', 'xvf', tar])
        if not self.dry_run:
            os.rename(tar, origtar)
            os.chdir(sourcedir)
        self.spawn(['debuild'])
        if not self.dry_run:
            os.chdir('..')
            shutil.rmtree(sourcedir, True)
            for i in glob.glob(name + '_' + debversion + '-*.build'):
                os.remove(i)
        deb = sorted(glob.glob(name + '_' + debversion + '-*_all.deb'))[-1]
        self.distribution.dist_files.append(('bdist_deb', 'any', deb))


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
