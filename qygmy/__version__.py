import os
import datetime
import subprocess

version_info = (0, 1, 0, 'alpha', 1)

def _get_version():
    v = '%s.%s' % version_info[:2]
    if version_info[2] != 0:
        v += '.%s' % version_info[2]
    v += '%s%s' % ({
        'alpha': 'a',
        'beta': 'b',
        'rc': 'c',
        'final': '',
    }[version_info[3]], version_info[4])

    if version_info[3] == 'alpha':
        v += '.dev' + _get_git_timestamp()

    return v

def _get_git_timestamp():
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    git_log = subprocess.Popen('git log --pretty=format:%ct --quiet -1 HEAD',
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=True, cwd=repo_dir, universal_newlines=True)
    timestamp = git_log.communicate()[0]
    try:
        timestamp = datetime.datetime.utcfromtimestamp(int(timestamp))
        timestamp = timestamp.strftime('%Y%m%d%H%M%S')
    except ValueError:
        timestamp = '0'
    timestamp_file = os.path.join(repo_dir, 'gittimestamp.txt')
    if timestamp != '0':
        with open(timestamp_file, 'w') as f:
            f.write(timestamp + '\n')
    elif os.path.isfile(timestamp_file):
        with open(timestamp_file, 'r') as f:
            timestamp = f.read().strip()
    return timestamp

version = _get_version()
