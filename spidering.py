# -*- coding: utf-8 -*-
import argparse
import sys

import requests_html as req

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('-f', metavar='XPATH', dest='filter')
    parser.add_argument('-o', metavar='DIR', dest='output')
    args = parser.parse_args()

    url = args.url
    output = args.output

    if not url:
        parser.print_help()
        sys.exit(1)

    exp = args.filter.rstrip()
    session = req.HTMLSession()
    resp = session.get(url)  # type:req.HTMLResponse
    resp.html.render(
        sleep=5,
        timeout=10
    )

    egg = set()
    try:
        for elem in resp.html.xpath(exp):
            if elem not in egg:
                egg.add(elem)
    except Exception as e:
        print('[-] {}'.format(e))
        sys.exit(1)

    if output:
        with open(output, "w") as f:
            f.write("\n".join(egg))
    else:
        for item in egg:
            print(item)
