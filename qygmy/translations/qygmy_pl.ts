<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE TS>
<TS version="2.0" language="pl">
<context>
    <name>Browser</name>
    <message>
        <location filename="../browser.py" line="117"/>
        <source>Details</source>
        <translation>Szczegóły</translation>
    </message>
</context>
<context>
    <name>Formatter</name>
    <message>
        <location filename="../formatter.py" line="29"/>
        <source>$if3(%paused%,[Paused] ,%stopped%,[Stopped] ,%connected%,[Connected] ,%disconnected%,[Disconnected])$if2(%file%,%directory%,%playlist%)</source>
        <translation>$if3(%paused%,[Pauza] ,%stopped%,[Zatrzymany] ,%connected%,[Połączony] ,%disconnected%,[Rozłączony])$if2(%file%,%directory%,%playlist%)</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="30"/>
        <source>$time(%length%)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="34"/>
        <source>$if($ne(%prio%,0),[High priority] ,)$if2(%file%,%directory%,%playlist%)</source>
        <translation>$if($ne(%prio%,0),[Wysoki priorytet] ,)$if2(%file%,%directory%,%playlist%)</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="40"/>
        <source>$if(%disconnected%,,%totalcount% songs$if($gt(%totallength%,0),\, $time(%totallength%) total,))</source>
        <translation>$if(%disconnected%,,%totalcount% utworów$if($gt(%totallength%,0),\, razem $time(%totallength%),))</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="42"/>
        <source>Songs:</source>
        <translation>Plików:</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="42"/>
        <source>%songs%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="43"/>
        <source>Albums:</source>
        <translation>Albumów:</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="43"/>
        <source>%albums%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="44"/>
        <source>Artists:</source>
        <translation>Artystów:</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="44"/>
        <source>%artists%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="45"/>
        <source>Uptime:</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="45"/>
        <source>$time(%uptime%)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="46"/>
        <source>DB playtime:</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="46"/>
        <source>$time(%db_playtime%)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="47"/>
        <source>This instance:</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="47"/>
        <source>$time(%playtime%)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="50"/>
        <source>%file%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="51"/>
        <source>Title:</source>
        <translation>Tytuł:</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="51"/>
        <source>%title%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="52"/>
        <source>Artist:</source>
        <translation>Artysta:</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="52"/>
        <source>%artist%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="53"/>
        <source>Album:</source>
        <translation>Album:</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="53"/>
        <source>%album%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="54"/>
        <source>Date:</source>
        <translation>Data:</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="54"/>
        <source>%date%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="55"/>
        <source>Track:</source>
        <translation>Ścieżka:</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="55"/>
        <source>%track%$if(%totaltracks%, / %totaltracks%,)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="56"/>
        <source>Disc:</source>
        <translation>Dysk:</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="56"/>
        <source>%disc%$if(%totaldiscs%, / %totaldiscs%,)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="57"/>
        <source>Comment:</source>
        <translation>Komentarz:</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="57"/>
        <source>%comment%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="58"/>
        <source>Length:</source>
        <translation>Czas:</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="58"/>
        <source>$if(%length%,$time(%length%),)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="59"/>
        <source>Last modified:</source>
        <translation>Ostatnio zmodyfikowany:</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="59"/>
        <source>%lastmodified%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="60"/>
        <source>Composer:</source>
        <translation>Kompozytor:</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="60"/>
        <source>%composer%</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../formatter.py" line="61"/>
        <source>Performer:</source>
        <translation>Wykonawca:</translation>
    </message>
    <message>
        <location filename="../formatter.py" line="61"/>
        <source>%performer%</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>Playlists</name>
    <message>
        <location filename="../lists.py" line="369"/>
        <source>New playlist</source>
        <translation>Nowa lista</translation>
    </message>
</context>
<context>
    <name>Qygmy</name>
    <message>
        <location filename="../qygmy.py" line="255"/>
        <source>Error</source>
        <translation>Błąd</translation>
    </message>
    <message>
        <location filename="../qygmy.py" line="247"/>
        <source>Save current playlist</source>
        <translation>Zapisz listę</translation>
    </message>
    <message>
        <location filename="../qygmy.py" line="248"/>
        <source>Playlist name:</source>
        <translation>Nazwa listy:</translation>
    </message>
    <message>
        <location filename="../qygmy.py" line="271"/>
        <source>About Qygmy</source>
        <translation>O Qygmy</translation>
    </message>
    <message>
        <location filename="../qygmy.py" line="257"/>
        <source>Playlist with such name already exists. Do you want to replace it?</source>
        <translation>Lista o tej nazwie już istnieje. Zastąpić?</translation>
    </message>
    <message>
        <location filename="../qygmy.py" line="277"/>
        <source>&lt;h2&gt;Qygmy&lt;/h2&gt;&lt;p&gt;version {version}&lt;/p&gt;&lt;p&gt;Simple MPD client written in Python and Qt/PySide.&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://github.com/tsufeki/qygmy&quot;&gt;https://github.com/tsufeki/qygmy&lt;/a&gt;&lt;/p&gt;</source>
        <translation>&lt;h2&gt;Qygmy&lt;/h2&gt;&lt;p&gt;wersja {version}&lt;/p&gt;&lt;p&gt;Prosty klient MPD napisany w Pythonie i Qt/PySide.&lt;/p&gt;&lt;p&gt;&lt;a href=&quot;https://github.com/tsufeki/qygmy&quot;&gt;https://github.com/tsufeki/qygmy&lt;/a&gt;&lt;/p&gt;</translation>
    </message>
</context>
<context>
    <name>Settings</name>
    <message>
        <location filename="../dialogs.py" line="70"/>
        <source>Qygmy$if(%playing%, / $if(%artist%,%artist% u2014 )$if2(%title%,%filename%))</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../dialogs.py" line="79"/>
        <source>$if3(%playing%%paused%,$time(%elapsed%)$if($and(%total%,$gt(%total%,0)), / $time(%total%)),%stopped%,Stopped,%connected%,Connected,Disconnected)</source>
        <translation>$if3(%playing%%paused%,$time(%elapsed%)$if($and(%total%,$gt(%total%,0)), / $time(%total%)),%stopped%,Zatrzymany,%connected%,Połączony,Rozłączony)</translation>
    </message>
    <message>
        <location filename="../dialogs.py" line="84"/>
        <source>&lt;span style=&quot;font-size: large; font-weight: bold&quot;&gt;$if2(%title%,%filename%)&lt;/span&gt;&lt;br&gt;%artist%$if(%album%, u2014 %album%)</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../dialogs.py" line="88"/>
        <source>$if(%artist%,%artist% u2014 )$if2(%title%,%filename%)</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>SonglistView</name>
    <message>
        <location filename="../uiutils.py" line="106"/>
        <source>Return</source>
        <translation type="unfinished"></translation>
    </message>
</context>
<context>
    <name>browser</name>
    <message>
        <location filename="../ui/browser.py" line="238"/>
        <source>Music database</source>
        <translation>Baza muzyki</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="239"/>
        <source>&amp;Database</source>
        <translation>&amp;Baza</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="240"/>
        <source>&amp;Playlists</source>
        <translation>&amp;Listy</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="241"/>
        <source>Tag to search</source>
        <translation>Szukany tag</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="242"/>
        <source>Any</source>
        <translation>Wszystko</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="243"/>
        <source>Title</source>
        <translation>Tytuł</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="244"/>
        <source>Artist</source>
        <translation>Artysta</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="245"/>
        <source>Album</source>
        <translation>Album</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="246"/>
        <source>Comment</source>
        <translation>Komentarz</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="247"/>
        <source>File name</source>
        <translation>Nazwa pliku</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="248"/>
        <source>&amp;Search</source>
        <translation>&amp;Szukaj</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="249"/>
        <source>&amp;Add selected</source>
        <translation>&amp;Dodaj zaznaczone</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="250"/>
        <source>Add selected songs to the current playlist</source>
        <translation>Dodaj zaznaczone utwory do głównej listy</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="251"/>
        <source>&amp;Close</source>
        <translation>&amp;Zamknij</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="252"/>
        <source>Close this window</source>
        <translation>Zamknij to okno</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="253"/>
        <source>Ctrl+W</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="254"/>
        <source>Search</source>
        <translation>Szukaj</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="255"/>
        <source>&amp;Remove selected</source>
        <translation>&amp;Usuń zaznaczone</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="256"/>
        <source>Del</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="257"/>
        <source>Add selected and &amp;play</source>
        <translation>Dodaj zaznaczone i &amp;odtwarzaj</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="258"/>
        <source>Shift+Return</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="259"/>
        <source>Song &amp;details...</source>
        <translation>&amp;Szczegóły...</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="260"/>
        <source>Ctrl+I</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="261"/>
        <source>Re&amp;name</source>
        <translation>Zmień &amp;nazwę</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="262"/>
        <source>F2</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="263"/>
        <source>R&amp;eplace the current playlist</source>
        <translation>Za&amp;stąp główną listę</translation>
    </message>
    <message>
        <location filename="../ui/browser.py" line="264"/>
        <source>Rep&amp;lace and play</source>
        <translation>Zas&amp;tąp i odtwarzaj</translation>
    </message>
</context>
<context>
    <name>infodialog</name>
    <message>
        <location filename="../ui/infodialog.py" line="60"/>
        <source>Details</source>
        <translation>Szczegóły</translation>
    </message>
</context>
<context>
    <name>main</name>
    <message>
        <location filename="../ui/main.py" line="327"/>
        <source>&amp;Playback</source>
        <translation>&amp;Odtwarzanie</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="328"/>
        <source>&amp;Volume</source>
        <translation>&amp;Głośność</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="329"/>
        <source>Pla&amp;ylist</source>
        <translation>&amp;Lista</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="330"/>
        <source>P&amp;revious</source>
        <translation>Pop&amp;rzedni</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="331"/>
        <source>Previous song</source>
        <translation>Poprzedni utwór</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="332"/>
        <source>Ctrl+P</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="333"/>
        <source>&amp;Play</source>
        <translation>&amp;Odtwarzaj</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="361"/>
        <source>Space</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="335"/>
        <source>&amp;Stop</source>
        <translation>&amp;Zatrzymaj</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="336"/>
        <source>Ctrl+S</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="337"/>
        <source>&amp;Next</source>
        <translation>&amp;Następny</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="338"/>
        <source>Next Song</source>
        <translation>Następny utwór</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="339"/>
        <source>Ctrl+N</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="340"/>
        <source>&amp;Add...</source>
        <translation>&amp;Dodaj...</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="341"/>
        <source>Add to playlist...</source>
        <translation>Dodaj do listy...</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="342"/>
        <source>Ctrl+L</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="343"/>
        <source>&amp;Remove</source>
        <translation>&amp;Usuń</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="344"/>
        <source>Remove selected</source>
        <translation>Usuń zaznaczone</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="345"/>
        <source>Del</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="346"/>
        <source>R&amp;epeat</source>
        <translation>Po&amp;wtarzaj</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="347"/>
        <source>S&amp;huffle</source>
        <translation>&amp;Losowo</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="348"/>
        <source>&amp;Settings...</source>
        <translation>&amp;Ustawienia...</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="349"/>
        <source>Ctrl+O</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="350"/>
        <source>Volume</source>
        <translation>Głośność</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="351"/>
        <source>&amp;Clear</source>
        <translation>&amp;Opróżnij</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="352"/>
        <source>Clear playlist</source>
        <translation>Opróżnij listę</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="353"/>
        <source>Dis&amp;connect from MPD</source>
        <translation>Rozłą&amp;cz z MPD</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="354"/>
        <source>&amp;Connect to MPD</source>
        <translation>Połą&amp;cz z MPD</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="355"/>
        <source>&amp;Update the database</source>
        <translation>Odśwież &amp;bazę</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="356"/>
        <source>S&amp;ingle track mode</source>
        <translation>&amp;Tryb pojedynczego utworu</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="357"/>
        <source>Single</source>
        <translation>Pojedyn.</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="358"/>
        <source>Re&amp;move songs after playback</source>
        <translation>U&amp;suń po odtworzeniu</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="359"/>
        <source>Consume</source>
        <translation>Usuń po</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="360"/>
        <source>&amp;Pause</source>
        <translation>P&amp;auzuj</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="362"/>
        <source>&amp;Save...</source>
        <translation>&amp;Zapisz</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="363"/>
        <source>Ctrl+T</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="364"/>
        <source>Song &amp;details...</source>
        <translation>&amp;Szczegóły</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="365"/>
        <source>Ctrl+I</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="366"/>
        <source>&amp;Quit</source>
        <translation>&amp;Wyjście</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="367"/>
        <source>Ctrl+Q</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="368"/>
        <source>Randomi&amp;ze</source>
        <translation>&amp;Wymieszaj</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="369"/>
        <source>&amp;MPD statistics...</source>
        <translation>Statystyki &amp;MPD...</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="370"/>
        <source>&amp;High priority</source>
        <translation>Wysoki &amp;priorytet</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="371"/>
        <source>Set high priority for selected songs</source>
        <translation>Odtwórz zaznaczone z wyższym priorytetem</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="372"/>
        <source>Ctrl+H</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="373"/>
        <source>&amp;Normal priority</source>
        <translation>&amp;Normalny priorytet</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="374"/>
        <source>Set normal priority for selected songs</source>
        <translation>Odtwórz zaznaczone ze zwykłym priorytetem</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="375"/>
        <source>Ctrl+J</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="376"/>
        <source>&amp;Louder</source>
        <translation>&amp;Głośniej</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="377"/>
        <source>Ctrl+E</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="378"/>
        <source>&amp;Quieter</source>
        <translation>&amp;Ciszej</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="379"/>
        <source>Ctrl+D</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="380"/>
        <source>&amp;About Qygmy...</source>
        <translation>O &amp;Qygmy...</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="381"/>
        <source>About Qt...</source>
        <translation>O Qt...</translation>
    </message>
    <message>
        <location filename="../ui/main.py" line="382"/>
        <source>Re&amp;verse</source>
        <translation>Odw&amp;róć</translation>
    </message>
</context>
<context>
    <name>settings</name>
    <message>
        <location filename="../ui/settings.py" line="184"/>
        <source>Settings</source>
        <translation>Ustawienia</translation>
    </message>
    <message>
        <location filename="../ui/settings.py" line="185"/>
        <source>MPD connection</source>
        <translation>Łączenie z MPD</translation>
    </message>
    <message>
        <location filename="../ui/settings.py" line="186"/>
        <source>Host:</source>
        <translation>Host:</translation>
    </message>
    <message>
        <location filename="../ui/settings.py" line="187"/>
        <source>Port:</source>
        <translation>Port:</translation>
    </message>
    <message>
        <location filename="../ui/settings.py" line="188"/>
        <source>Password:</source>
        <translation>Hasło:</translation>
    </message>
    <message>
        <location filename="../ui/settings.py" line="189"/>
        <source>Interface options</source>
        <translation>Opcje interfejsu</translation>
    </message>
    <message>
        <location filename="../ui/settings.py" line="190"/>
        <source>Auto-scroll on song change:</source>
        <translation>Przewijaj automatycznie przy zmianie utworu:</translation>
    </message>
    <message>
        <location filename="../ui/settings.py" line="191"/>
        <source>Updating interval:</source>
        <translation>Okres odświeżania:</translation>
    </message>
    <message>
        <location filename="../ui/settings.py" line="192"/>
        <source> ms</source>
        <translation> ms</translation>
    </message>
    <message>
        <location filename="../ui/settings.py" line="193"/>
        <source>Formatting</source>
        <translation>Formatowanie</translation>
    </message>
    <message>
        <location filename="../ui/settings.py" line="195"/>
        <source>Current song</source>
        <translation>Aktualny utwór</translation>
    </message>
    <message>
        <location filename="../ui/settings.py" line="196"/>
        <source>Playlist item</source>
        <translation>Element listy</translation>
    </message>
    <message>
        <location filename="../ui/settings.py" line="197"/>
        <source>Progress bar</source>
        <translation>Pasek</translation>
    </message>
    <message>
        <location filename="../ui/settings.py" line="198"/>
        <source>Window title</source>
        <translation>Tytuł okna</translation>
    </message>
    <message>
        <location filename="../ui/settings.py" line="194"/>
        <source>Help:&lt;ul style=&quot;margin: 0&quot;&gt;&lt;li&gt;&lt;a href=&quot;https://github.com/tsufeki/qygmy/blob/master/doc/templates.md&quot;&gt;https://github.com/tsufeki/qygmy/blob/master/doc/templates.md&lt;/a&gt;&lt;/li&gt;&lt;li&gt;&lt;a href=&quot;https://qt-project.org/doc/qt-4.8/richtext-html-subset.html&quot;&gt;https://qt-project.org/doc/qt-4.8/richtext-html-subset.html&lt;/a&gt;&lt;/li&gt;&lt;/ul&gt;</source>
        <translation>Pomoc:&lt;ul style=&quot;margin: 0&quot;&gt;&lt;li&gt;&lt;a href=&quot;https://github.com/tsufeki/qygmy/blob/master/doc/templates.md&quot;&gt;https://github.com/tsufeki/qygmy/blob/master/doc/templates.md&lt;/a&gt;&lt;/li&gt;&lt;li&gt;&lt;a href=&quot;https://qt-project.org/doc/qt-4.8/richtext-html-subset.html&quot;&gt;https://qt-project.org/doc/qt-4.8/richtext-html-subset.html&lt;/a&gt;&lt;/li&gt;&lt;/ul&gt;</translation>
    </message>
</context>
<context>
    <name>templates</name>
    <message>
        <location filename="../templates/template.py" line="150"/>
        <source>{}{}d {:02d}:{:02d}:{:02d}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../templates/template.py" line="151"/>
        <source>{}{}:{:02d}:{:02d}</source>
        <translation type="unfinished"></translation>
    </message>
    <message>
        <location filename="../templates/template.py" line="152"/>
        <source>{}{:02d}:{:02d}</source>
        <translation type="unfinished"></translation>
    </message>
</context>
</TS>
