import argparse
import html
import os
import re
import shutil
import sys

from pytube import Stream
from pytube import YouTube


class YoutubeManager:

    def __init__(self, url):
        self._yt, self._streams = self._fetch_all(url)
        self._sel = None  # type:Stream
        self._inf = {}

    def _select(self, s):
        self._sel = s[0]
        self._inf['type'] = s[1]
        self._inf['format'] = s[2]
        self._inf['quality'] = s[3]
        self._inf['size'] = s[4]

    @staticmethod
    def _fetch_all(url):
        results = []
        yt = YouTube(url)
        all_streams = yt.streams
        for s in all_streams:
            quality = s.resolution if s.resolution else s.abr
            if quality:
                results.append(
                    (s, s.type, s.mime_type.split('/')[-1], quality, '{:.2f}MB'.format(s.filesize / 1048576)))

        return yt, results

    @property
    def filename(self):
        return self._sanity_filename(self.title)

    @property
    def streaminfo(self):
        return self._inf

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
        return re.sub(r'[\/:*?."<>|#]+', '', s)

    def _only_video(self):
        res = []
        for s in self.streams:
            if s[1] == 'video':
                res.append(s)
        return sorted(res, key=lambda a: int(a[3][:-1]), reverse=True)

    def _only_audio(self):
        res = []
        for s in self.streams:
            if s[1] == 'audio':
                res.append(s)
        return sorted(res, key=lambda a: int(a[3][:-4]), reverse=True)

    def best_audio(self):
        for s in self._only_audio():
            if s[2] == 'mp4':
                self._select(s)
                return self

    def best_video(self):
        for s in self._only_video():
            if s[2] == 'mp4' and s[0].progressive is True:
                self._select(s)
                return self

    def stream_at(self, idx):
        s = self.streams[idx]
        self._select(s)
        return self

    def download(self, path, on_progress=None):
        if not self.selection:
            raise Exception('cannot found any stream')

        if on_progress:
            # function=on_progress,args=(stream: Stream, chunk: bytes, bytes_remaining: int)
            self._yt.register_on_progress_callback(on_progress)

        self._sel.download(path, self._sanity_filename(self.title))


def render_progress_bar(bytes_recv, filesize, ch='\u258c', scale=0.55):
    cols = shutil.get_terminal_size().columns
    max_width = int(cols * scale)
    filled = int(round(max_width * bytes_recv / float(filesize)))
    remaining = max_width - filled
    progress_bar = ch * filled + ' ' * remaining
    percent = round(100.0 * bytes_recv / float(filesize), 1)
    print('\r {p}% |{ch}| {recv:.3f}MB/{size:.3f}MB'.format(ch=progress_bar,
                                                            p=percent, recv=bytes_recv / 1048576,
                                                            size=filesize / 1048576), end='\r')
    sys.stdout.flush()


def on_progress(stream: Stream, chunk: bytes, bytes_remaining: int):
    filesize = stream.filesize
    bytes_recv = filesize - bytes_remaining
    render_progress_bar(bytes_recv, filesize, scale=0.1)


def main(args):
    url = args.url
    # TODO: assert URL is not None

    path = os.path.dirname(os.path.realpath(__file__))

    print('[+] loading video... ', end='')
    try:
        mgr = YoutubeManager(url)

        print('done')
        print('[i] {}'.format(mgr.title))

        if args.s:

            header = ['stream', 'type', 'format', 'quality', 'size']
            print('{h[0]:10}{h[1]:10}{h[2]:10}{h[3]:10}{h[4]:10}'.format(h=header))
            for i, data in enumerate(mgr.streams):
                print('{:10}{d[1]:10}{d[2]:10}{d[3]:10}{d[4]:10}'.format(str(i), d=data))

            return

        if args.a:
            mgr.best_audio()

        if args.b:
            mgr.best_video()

        if args.n:
            mgr.stream_at(args.n)

        print('[+] downloading... ')
        mgr.download(path, on_progress)

        print('\ndone')
    except Exception as e:
        print('fail')
        print('[!] {}'.format(e))


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('-s', action='store_true')
    parser.add_argument('-a', action='store_true')
    parser.add_argument('-b', action='store_true')
    parser.add_argument('-n', type=int)
    return parser.parse_args()


if __name__ == '__main__':
    main(get_args())
