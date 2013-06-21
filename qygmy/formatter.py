
from PySide.QtGui import QIcon

from .templates import Template


class Formatter:

    _directory_icon = QIcon.fromTheme('folder')
    _playlist_icon = QIcon.fromTheme('text-plain')

    templates = {
        'window_title': (
            '[Qygmy]'
            '$if(%playing%, '
            '$if2(%title%,%filename%)'
            '$if(%artist%, / %artist%,),)'
        ),
        'progressbar': (
            '$if3('
                '%playing%%paused%,'
                    '$time(%elapsed%)'
                    '$if($and(%total%,$gt(%total%,0)), / $time(%total%),),'
                '%stopped%,Stopped,'
                '%connected%,Connected,'
                'Disconnected)'
        ),
        'current_song': (
            '<span style="font-size: big; font-weight: bold">'
                '$if2(%title%,%filename%)</span><br>'
            '<span style="font-size: small">'
                '%artist%</span><br>'
            '<span style="font-size: small">'
                '%comment%$if($and(%comment%,%album%),\xa0\xa0/\xa0\xa0,)%album%</span>'
        ),
        '_current_song_tooltip': (
            '$if3(%paused%,[Paused] ,'
                '%stopped%,[Stopped] ,'
                '%connected%,[Connected] ,'
                '%disconnected%,[Disconnected])'
            '$if2(%file%,%directory%,%playlist%)'
        ),
        'playlist_item': (
            '$if2(%title%,%filename%)'
            '$if(%artist%,'
                '<span style="color: gray">\xa0\xa0/\xa0\xa0</span>%artist%,)'
            '$if(%album%%comment%,'
                '<br><span style="color: gray; font-size: small">\xa0\xa0\xa0'
                '%comment%'
                '$if($and(%album%,%comment%),\xa0\xa0/\xa0\xa0,)'
                '%album%</span>,)'
        ),
        '_playlist_column2': '$time(%length%)',
        '_playlist_tooltip': '$if2(%file%,%directory%,%playlist%)',
        '_status': (
            '$if(%disconnected%,,'
                '%totalcount% songs'
                '$if($gt(%totallength%,0),'
                    '\\, $time(%totallength%) total,))'
        ),
        '_statistics': (
            ('Songs:', '%songs%'),
            ('Albums:', '%albums%'),
            ('Artists:', '%artists%'),
            ('Uptime:', '$time(%uptime%)'),
            ('DB playtime:', '$time(%db_playtime%)'),
            ('This instance:', '$time(%playtime%)'),
        ),
        '_details': (
            ('Path:', '%file%'),
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

    def _escape(self, s):
        return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    def _prepare_song(self, song, html=True):
        song = song.copy()
        song.pop('id', None)
        song.pop('pos', None)
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
            'left': str(max(total - elapsed, 0)),
        }

    def _compile(self, template):
        pref = '$if(%bold%,<span style="font-weight: bold">,)'
        suff = '$if(%bold%,</span>,)'
        if isinstance(template, str):
            return Template(pref + template + suff)
        return tuple((self._compile(a), self._compile(b)) for a, b in template)

    def _render(self, template, context):
        if isinstance(template, Template):
            return template.render(context)
        return [(self._render(a, context), self._render(b, context)) for a, b in template]

    def render(self, name, context, bold=False):
        if not hasattr(self, '_tmplcache'):
            self._tmplcache = {}
        if name not in self._tmplcache:
            self._tmplcache[name] = self._compile(self.templates[name])
        tmpl = self._tmplcache[name]
        context['bold'] = '1' if bold else ''
        return self._render(tmpl, context)

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
        return self.render('_current_song_tooltip', context)

    def playlist_item(self, song, column, is_current=False):
        if column == 0:
            return self.render('playlist_item', self._prepare_song(song), bold=is_current)
        elif column == 1 and 'time' in song:
            return self.render('_playlist_column2', {'length': song['time']}, bold=is_current)
        return ''

    def playlist_icon(self, song, column, is_current=False):
        if column == 0:
            if 'playlist' in song:
                return self._playlist_icon
            if 'directory' in song:
                return self._directory_icon

    def playlist_tooltip(self, song, column, is_current=False):
        return self.render('_playlist_tooltip', self._prepare_song(song, html=False))

    def status(self, state, totallength, totalcount):
        context = {'totallength': str(totallength), 'totalcount': str(totalcount)}
        context.update(self._prepare_state(state))
        return self.render('_status', context)

    def info_dialog(self, name, info):
        if name == 'details':
            info = self._prepare_song(info, html=False)
        r = self.render('_' + name, info)
        return [i for i in r if i[1] != '']

    @property
    def playlist_column_count(self):
        return 2


    def _details(self, song):
        mblink = lambda typ: lambda x: '<a href="http://musicbrainz.org/{0}/{1}">{1}</a>'.format(typ, x)
        ('musicbrainz_trackid', 'MB track id', mblink('recording')),
        ('musicbrainz_albumid', 'MB album id', mblink('release')),
        ('musicbrainz_artistid', 'MB artist id', mblink('artist')),
        ('musicbrainz_albumartistid', 'MB album artist id', mblink('artist')),

