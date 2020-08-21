import argparse
import os
from pytube import YouTube


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('-s', action='store_true')
    parser.add_argument('-a', action='store_true')
    parser.add_argument('-b', action='store_true')
    parser.add_argument('-n', type=int, default=-1)
    return parser.parse_args()


def main(args):
    url = args.url
    # TODO: assert URL is not None

    path = os.path.dirname(os.path.abspath(__file__))

    results = []

    yt = YouTube(url)
    streams = yt.streams
    for s in streams:
        quality = s.resolution if s.resolution else s.abr
        results.append((s.itag, s.type, s.mime_type.split('/')[-1], quality, s.filesize))

    if args.s:
        for i, e in enumerate(results):
            print('{:>4}{}'.format(i, e))
        return
    if args.a:
        return
    if args.b:
        return
    if args.n >= 0:
        return


if __name__ == '__main__':
    main(get_args())
