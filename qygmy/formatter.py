
from PySide.QtGui import QIcon

from .templates import Template


class Formatter:

    _directory_icon = QIcon.fromTheme('folder')
    _playlist_icon = QIcon.fromTheme('text-plain')

    templates = {
        'playlist_entry': Template('%title%$if(%artist%,  <span style="color: gray">/</span>  %artist%,)'
            '$if($or(%album%,%comment%),\n<span style="color: gray; font-size: small">'
            '%comment%$if($and(%album%,%comment%),  /  ,)%album%</span>,)'),
        'current_song': Template('<span style="font-size: big; font-weight: bold">%title%</span>\n'
            '<span style="font-size: small">%artist%</span>\n'
            '<span style="font-size: small">%comment%$if($and(%comment%,%album%),  /  ,)%album%</span>'),
        'folder_entry': Template('%filename%'),
        'progressbar': Template('%elapsed%$if(%total%, / %total%,)'),
    }

    def _escape(self, s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def _time(self, seconds):
        seconds = int(seconds)
        s = seconds % 60
        m = (seconds // 60) % 60
        h = seconds // 3600
        time = '{:02d}:{:02d}'.format(m, s)
        if h == 0:
            return time
        return '{}:{}'.format(h, time)

    def _prepare(self, metadata, escape=True):
        metadata = metadata.copy()
        metadata.pop('id', None)
        metadata.pop('pos', None)
        metadata.pop('last-modified', None)
        if 'time' in metadata:
            metadata['length'] = self._time(int(metadata.pop('time')))
        for key in ['file', 'directory', 'playlist']:
            if key in metadata:
                fullpath = metadata[key]
                filename = fullpath.rsplit('/', 1)[-1]
                if fullpath:
                    metadata['fullpath'] = fullpath
                if filename:
                    metadata['filename'] = filename
        if not metadata.get('title') and metadata.get('filename'):
            metadata['title'] = filename
        if 'track' in metadata and '/' in metadata['track']:
            metadata['track'], metadata['totaltracks'] = metadata['track'].split('/', 1)
        if 'disc' in metadata and '/' in metadata['disc']:
            metadata['disc'], metadata['totaldiscs'] = metadata['disc'].split('/', 1)
        if 'elapsed' in metadata and 'total' in metadata:
            metadata['left'] = self._time(int(metadata['total']) - int(metadata['elapsed']))
        if 'elapsed' in metadata:
            metadata['elapsed'] = self._time(int(metadata['elapsed']))
        if 'total' in metadata:
            metadata['total'] = self._time(int(metadata['total']))
        for k, v in metadata.items():
            if isinstance(v, (list, tuple)):
                v = ', '.join(v)
            if escape:
                v = self._escape(v)
            metadata[k] = v
        return metadata

    def _render(self, metadata, template, html=True, bold=False):
        metadata = self._prepare(metadata, html)
        r = self.templates[template].render(metadata)
        if html and bold:
            r = '<span style="font-weight: bold !important">{}</span>'.format(r)
        if html:
            r = '<span style="white-space: pre">{}</span>'.format(r)
        return r

    def progressbar(self, times):
        e, t = times
        text = self._render({'elapsed': e, 'total': t}, 'progressbar', html=False)
        if e == t == 0:
            t = 1
        return text, e, t

    def progressbar_notplaying(self, state):
        if state == 'disconnect':
            return 'Disconnected'
        return 'Stopped'

    def playlist_entry(self, metadata, column, is_current=False):
        if 'directory' in metadata or 'playlist' in metadata:
            if column == 0:
                return self._render(metadata, 'folder_entry')
        else:
            if column == 0:
                return self._render(metadata, 'playlist_entry', bold=is_current)
            elif column == 1:
                return self._time(int(metadata.get('time', '0')))
        return ''

    def playlist_icon(self, data, column, is_current=False):
        if column == 0:
            if 'playlist' in data:
                return self._playlist_icon
            if 'directory' in data:
                return self._directory_icon

    def playlist_tooltip(self, song, column, is_current=False):
        return song.get('file')

    def main_window_title(self, song):
        return 'Qygmy'

    def browser_window_title(self, path=''):
        path = self._escape(path.rsplit('/', 1)[-1])
        if path:
            return 'Music database - %s' % path
        else:
            return 'Music database'

    def current_song(self, song):
        return self._render(song, 'current_song')

    @property
    def playlist_column_count(self):
        return 2

    def details(self, song):
        song = song.copy()
        song.pop('id', None)
        song.pop('pos', None)
        s = '<table>'
        s += '<tr><td colspan=2>{}</td></tr>'.format(song.pop('file', ''))
        s += '<tr><td colspan=2></td></tr>'
        mblink = lambda typ: lambda x: '<a href="http://musicbrainz.org/{0}/{1}">{1}</a>'.format(typ, x)
        for key, display, xform in [
            ('title', 'Title', self._escape),
            ('artist', 'Artist', self._escape),
            ('album', 'Album', self._escape),
            ('date', 'Date', self._escape),
            ('track', 'Track', self._escape),
            ('disc', 'Disc', self._escape),
            ('comment', 'Comment', self._escape),
            ('time', 'Length', self._time),
            ('last-modified', 'Last modified', lambda x: x.replace('T', ' ').replace('Z', '')),
            ('composer', 'Composer', self._escape),
            ('performer', 'Performer', self._escape),
            ('musicbrainz_trackid', 'MB track id', mblink('recording')),
            ('musicbrainz_albumid', 'MB album id', mblink('release')),
            ('musicbrainz_artistid', 'MB artist id', mblink('artist')),
            ('musicbrainz_albumartistid', 'MB album artist id', mblink('artist')),
        ]:
            v = song.pop(key, '')
            if v:
                if isinstance(v, (list, tuple)):
                    v = ', '.join(v)
                s += (
                    '<tr>'
                        '<td style="'
                            'padding-top: 5px;'
                            'white-space: nowrap;'
                            'font-weight: bold;'
                        '">{}:</td>'
                        '<td style="'
                            'padding-top: 5px;'
                        '">{}</td>'
                    '</tr>'
                ).format(display, xform(v))
        for key in sorted(song.keys()):
            s += (
                '<tr>'
                    '<td style="padding-top: 5px;">{}:</td>'
                    '<td style="padding-top: 5px;">{}</td>'
                '</tr>'
            ).format(key, song[key])
        s += '</table>'
        return s

