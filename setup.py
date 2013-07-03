
import os
from distutils.core import setup
from distutils.command.build import build
from distutils.command.clean import clean
from distutils.spawn import spawn

from qygmy.__version__ import version
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


setup(
    name = 'Qygmy',
    version = version,
    description = "Simple MPD client.",
    long_description = """
Simple MPD client written in Qt/PySide.
""",
    author = 'tsufeki',
    author_email = 'tsufeki@ymail.com',
    url = 'https://github.com/tsufeki/qygmy',
    packages = [
        'qygmy',
        'qygmy.templates',
        'qygmy.ui',
    ],
    package_data={
        'qygmy': ['translations/*.qm', 'gittimestamp.txt'],
    },
    install_requires=[
        #'PySide>=1.1.2',
        'python-mpd2',
    ],
    scripts=['bin/qygmyrun'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: End Users/Desktop',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Topic :: Multimedia :: Sound/Audio',
    ],
    cmdclass={
        'clean': clean,
        'build': build,
    },
)
