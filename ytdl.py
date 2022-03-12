#!/usr/bin/python
'''
Description:
The command-line utility for downloading Youtube video or audio
    
Prerequisites:
- "ffmpeg"
    
If the libraries are not installed just run the following command in your terminal:
- On Linux(Ubuntu): apt-get install ffmpeg
'''

import argparse
import html
import re
import shutil
import os
import sys
import time

while True:
    try:
        from pytube import Stream, YouTube, Playlist
        
        break
    except ImportError:
        os.system('pip install pytube')


class YoutubeManager:

    def __init__(self, url):
        self._yt, self._streams = self._fetch_all(url)
        self._sel = None

    @staticmethod
    def _fetch_all(url):
        results = []
        yt = YouTube(url)
        all_streams = yt.streams
        for s in all_streams:
            quality = s.resolution if s.resolution else s.abr
            if quality:
                results.append((
                    s,
                    {
                        'itag': s.itag,
                        'type': s.type,
                        'format': s.mime_type.split('/')[-1],
                        'quality': quality,
                        'size': '{:.2f}MB'.format(s.filesize / 1048576),
                        'progressive': 'true' if s.is_progressive else ''
                    }
                ))

        return yt, results

    @property
    def filename(self):
        return self._sanity_filename(self._yt.title)

    @property
    def title(self):
        return self._yt.title

    @property
    def streams(self):
        return self._streams

    @property
    def selection(self):
        return self._sel

    @staticmethod
    def _sanity_filename(s):
        s = html.unescape(s)
        return re.sub(r'[\/:*?.,"<>|#]+', '', s)

    def _only_video(self):
        res = []
        for s in self.streams:
            if s[1]['type'] == 'video':
                res.append(s)
        return sorted(res, key=lambda a: int(a[1]['quality'][:-1]), reverse=True)

    def _only_audio(self):
        res = []
        for s in self.streams:
            if s[1]['type'] == 'audio':
                res.append(s)
        return sorted(res, key=lambda a: int(a[1]['quality'][:-4]), reverse=True)

    def best_audio(self):
        for s in self._only_audio():
            if s[1]['format'] == 'mp4':
                self._sel = s
                return self

    def best_video(self):
        for s in self._only_video():
            if s[1]['format'] == 'mp4' and s[1]['progressive'] == 'true':
                self._sel = s
                return self

    def stream_at(self, itag):
        for s in self.streams:
            if s[1]['itag'] == itag:
                self._sel = s
                break
        return self

    def download(self, path, on_progress=None):
        if not self.selection:
            raise Exception('cannot found any stream')

        if on_progress:
            """function=on_progress,args=(stream: Stream, chunk: bytes, bytes_remaining: int)"""
            self._yt.register_on_progress_callback(on_progress)

        self._sel[0].download(path, self._sanity_filename(self.title))


class ProgressBar():
    def __init__(self):
        self._start_seconds = time.time()

    def _render(self, bytes_recv, filesize, ch='\u2588', scale=0.55):
        cols = shutil.get_terminal_size().columns
        max_width = int(cols * scale)
        filled = int(round(max_width * bytes_recv / float(filesize)))
        remaining = max_width - filled
        progress_bar = ch * filled + ' ' * remaining
        percent = int(round(100.0 * bytes_recv / float(filesize), 1))

        megabytes_recv = bytes_recv / 1048576
        elapsed_seconds = time.time() - self._start_seconds

        sys.stdout.write('\r {p}% |{ch}| {recv:.3f}MB/{size:.3f}MB [{spd:.3f}MB/sec]'.format(ch=progress_bar,
                                                                                             p=percent,
                                                                                             recv=megabytes_recv,
                                                                                             size=filesize / 1048576,
                                                                                             spd=megabytes_recv / elapsed_seconds))
        sys.stdout.flush()

    def __call__(self, stream: Stream, chunk: bytes, bytes_remaining: int):
        filesize = stream.filesize
        bytes_recv = filesize - bytes_remaining
        self._render(bytes_recv, filesize, scale=0.25)


def main():
    'Youtube download tool'

    parser = argparse.ArgumentParser(description=main.__doc__)
    parser.add_argument('url', help='Youtube video URL to download')
    parser.add_argument('-o', metavar='PATH',
                        help='output path for writing media file (default to the current working directory)')
    parser.add_argument('-s', action='store_true', help='display available streams')
    parser.add_argument('-a', action='store_true', help='download the best quality audio (ignore -n)')
    parser.add_argument('-b', action='store_true', help='download the best quality video (ignore -n)')
    parser.add_argument('-n', metavar='N', type=int,
                        help='specify stream to download by stream number (use -s to list available streams)')

    args = parser.parse_args()

    url = args.url.strip()

    if not url or 'youtu' not in url:
        parser.print_help()
        return

    path = args.o if args.o else os.getcwd()

    print('[+] Loading video... ', end='')
    try:
        mgr = YoutubeManager(url)

        print('Done')
        print('[i] {}'.format(mgr.title))

        if args.s:

            header = ['stream', 'type', 'format', 'quality', 'size', 'progressive']
            print('{h[0]:10}{h[1]:10}{h[2]:10}{h[3]:10}{h[4]:10}{h[5]:10}'.format(h=header))
            print('-' * 61)
            for stream in mgr.streams:
                s = stream[1]
                print(
                    '{:<10}{:10}{:10}{:10}{:10}{:10}'.format(s['itag'], s['type'], s['format'], s['quality'],
                                                             s['size'],
                                                             s['progressive']))

            return

        if args.a:
            mgr.best_audio()

        if args.b:
            mgr.best_video()

        if args.n:
            mgr.stream_at(args.n)

        print('\n')
        print(f'[+] Downloading @itag={mgr.selection[1]["itag"]}')
        on_progress = ProgressBar()
        mgr.download(path, on_progress)
        f_name = os.path.join(path, mgr.filename)
        if os.path.isfile(f_name):
            f_name = f_name + '.mp4'

        if args.a:
            print('[+] Converting to mp3')            
            os.system(f'ffmpeg -i "{f_name}.mp4" "{f_name} [uncompleted].mp3" -hide_banner')
            os.remove(f_name + '.mp4')
            os.rename(f'{f_name} [uncompleted].mp3', f_name + '.mp3')

        print('[+] Download completed!')
    except Exception as e:
        print('Fail')
        print(f'[-] {e}')


if __name__ == '__main__':
    main()
