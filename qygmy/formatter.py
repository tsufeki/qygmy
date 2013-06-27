
from PySide.QtGui import QIcon, QBrush, QColor

from .templates import Template


class Formatter:

    def __init__(self, settings):
        self.settings = settings
        self._tmplcache = {}

    _directory_icon = QIcon.fromTheme('folder')
    _playlist_icon = QIcon.fromTheme('text-plain')
    _high_prio_background = QBrush(QColor(255, 255, 0, 127))

    playlist_column_count = 2

    templates = {
        'current_song_tooltip': (
            '$if3(%paused%,[Paused] ,'
                '%stopped%,[Stopped] ,'
                '%connected%,[Connected] ,'
                '%disconnected%,[Disconnected])'
            '$if2(%file%,%directory%,%playlist%)'
        ),
        'playlist_column2': '$time(%length%)',
        'playlist_tooltip': (
            '$if($ne(%prio%,0),[High priority] ,)'
            '$if2(%file%,%directory%,%playlist%)'
        ),
        'status': (
            '$if(%disconnected%,,'
                '%totalcount% songs'
                '$if($gt(%totallength%,0),'
                    '\\, $time(%totallength%) total,))'
        ),
        'statistics': (
            ('Songs:', '%songs%'),
            ('Albums:', '%albums%'),
            ('Artists:', '%artists%'),
            ('Uptime:', '$time(%uptime%)'),
            ('DB playtime:', '$time(%db_playtime%)'),
            ('This instance:', '$time(%playtime%)'),
        ),
        'details': (
            ('%file%', None),
            ('Title:', '%title%'),
            ('Artist:', '%artist%'),
            ('Album:', '%album%'),
            ('Date:', '%date%'),
            ('Track:', '%track%$if(%totaltracks%, / %totaltracks%,)'),
            ('Disc:', '%disc%$if(%totaldiscs%, / %totaldiscs%,)'),
            ('Comment:', '%comment%'),
            ('Length:', '$if(%length%,$time(%length%),)'),
            ('Last modified:', '%lastmodified%'),
            ('Composer:', '%composer%'),
            ('Performer:', '%performer%'),
        )
    }

    standard_tags = {'file', 'directory', 'playlist', 'filename', 'title',
        'artist', 'album', 'date', 'track', 'totaltracks', 'disc', 'totaldiscs',
        'comment', 'length', 'lastmodified', 'composer', 'performer',
    }

    def _escape(self, s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def _prepare_song(self, song, html=True):
        song = song.copy()
        song.pop('id', None)
        song.pop('pos', None)
        if 'prio' not in song:
            song['prio'] = '0'
        for key in ['file', 'directory', 'playlist']:
            if key in song:
                filename = song[key].rsplit('/', 1)[-1]
                if filename:
                    song['filename'] = filename
        if 'time' in song:
            song['length'] = int(song.pop('time'))
        if 'track' in song and '/' in song['track']:
            song['track'], song['totaltracks'] = song['track'].split('/', 1)
        if 'disc' in song and '/' in song['disc']:
            song['disc'], song['totaldiscs'] = song['disc'].split('/', 1)
        if 'last-modified' in song:
            song['lastmodified'] = song.pop('last-modified').replace('T', ' ').replace('Z', '')
        ret = {}
        for k, v in song.items():
            if isinstance(v, (list, tuple)):
                v = ', '.join(v)
            else:
                v = str(v)
            if html:
                v = self._escape(v)
            if v != '':
                ret[k] = v
        return ret

    def _prepare_state(self, state):
        return {{
            'play': 'playing',
            'pause': 'paused',
            'stop': 'stopped',
            'disconnect': 'disconnected',
            'connect': 'connected',
        }[state]: '1'}

    def _prepare_times(self, elapsed, total):
        return {
            'elapsed': str(elapsed),
            'total': str(total),
        }

    def _compile(self, template):
        pref = '$if(%bold%,<span style="font-weight: bold">,)'
        suff = '$if(%bold%,</span>,)'
        if isinstance(template, str):
            return Template(pref + template + suff)
        r = []
        for a, b in template:
            a = self._compile(a)
            if b is not None:
                b = self._compile(b)
            r.append((a, b))
        return tuple(r)

    def _render(self, template, context):
        if isinstance(template, Template):
            return template.render(context)
        r = []
        for a, b in template:
            a = self._render(a, context)
            if b is not None:
                b = self._render(b, context)
            r.append((a, b))
        return r

    def render(self, name, context, bold=False):
        tmpl = self._tmplcache.get(name)
        if tmpl is None:
            if name in self.settings['format']:
                t = self.settings['format'][name]
            else:
                t = self.templates[name]
            tmpl = self._tmplcache[name] = self._compile(t)
        context['bold'] = '1' if bold else ''
        return self._render(tmpl, context)

    def clear_cache(self):
        self._tmplcache.clear()

    def window_title(self, state, song):
        context = self._prepare_state(state)
        context.update(self._prepare_song(song, html=False))
        return self.render('window_title', context)

    def progressbar(self, state, elapsed, total, song):
        context = self._prepare_state(state)
        context.update(self._prepare_times(elapsed, total))
        context.update(self._prepare_song(song, html=False))
        return self.render('progressbar', context)

    def current_song(self, state, song):
        context = self._prepare_state(state)
        context.update(self._prepare_song(song))
        return self.render('current_song', context)

    def current_song_tooltip(self, state, song):
        context = self._prepare_state(state)
        context.update(self._prepare_song(song, html=False))
        return self.render('current_song_tooltip', context)

    def playlist_item(self, song, column, is_current):
        if column == 0:
            return self.render('playlist_item', self._prepare_song(song), bold=is_current)
        elif column == 1 and 'time' in song:
            return self.render('playlist_column2', {'length': song['time']}, bold=is_current)
        return ''

    def playlist_icon(self, song, column, is_current):
        if column == 0:
            if 'playlist' in song:
                return self._playlist_icon
            if 'directory' in song:
                return self._directory_icon

    def playlist_tooltip(self, song, column, is_current):
        return self.render('playlist_tooltip', self._prepare_song(song, html=False))

    def playlist_background(self, song, column, is_current):
        if song.get('prio', '0') != '0':
            return self._high_prio_background

    def status(self, state, totallength, totalcount):
        context = {'totallength': str(totallength), 'totalcount': str(totalcount)}
        context.update(self._prepare_state(state))
        return self.render('status', context)

    def info_dialog(self, name, info):
        unrecognized = []
        if name == 'details':
            info = self._prepare_song(info, html=False)
            info.pop('prio', None)
            for k, v in info.items():
                if k not in self.standard_tags and k and v:
                    unrecognized.append((k + ':', v))
        r = [i for i in self.render(name, info) if i[1] != '']
        return r + unrecognized

