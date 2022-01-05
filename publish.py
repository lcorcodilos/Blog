#! /usr/bin/env python3
'''Script to publish a draft to posts.
Prepends the current date and pushes to GitHub.
'''

import subprocess, sys
from datetime import datetime

def cmd(c):
    print (c)
    subprocess.call(c.split(' '))

if __name__ == '__main__':
    to_publish = [p.split('/')[-1] for p in sys.argv[1:]]
    for p in to_publish:
        cmd(f'mv _drafts/{p} _posts/{datetime.now().year:04}-{datetime.now().month:02}-{datetime.now().day:02}-{p}')