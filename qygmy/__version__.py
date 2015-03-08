
import os
import datetime
import subprocess

version_info = (1, 2, 0, 'alpha', 0)

def _get_version():
    v = '%s.%s' % version_info[:2]
    if version_info[2] != 0:
        v += '.%s' % version_info[2]
    v += {
        'alpha': 'a',
        'beta': 'b',
        'rc': 'c',
        'final': '',
    }[version_info[3]]
    if version_info[3] != 'final' and version_info[4] != 0:
        v += str(version_info[4])

    repo_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp_file = os.path.join(repo_dir, 'gittimestamp.txt')

    if version_info[3] == 'alpha':
        git_log = subprocess.Popen('git log --pretty=format:%ct --quiet -1 HEAD',
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=True, cwd=repo_dir, universal_newlines=True)
        timestamp = git_log.communicate()[0]
        try:
            timestamp = datetime.datetime.utcfromtimestamp(int(timestamp))
            timestamp = timestamp.strftime('%Y%m%d%H%M%S')
        except ValueError:
            timestamp = '0'
        if timestamp != '0':
            with open(timestamp_file, 'w') as f:
                f.write(timestamp + '\n')
        elif os.path.isfile(timestamp_file):
            with open(timestamp_file, 'r') as f:
                timestamp = f.read().strip()
        v += '.dev' + timestamp

    else:
        try:
            os.remove(timestamp_file)
        except:
            pass

    return v

version = _get_version()
