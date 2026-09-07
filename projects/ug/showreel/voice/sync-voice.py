#!/usr/bin/env python3
"""Make the films speak the script.

The narration lived in three places that drifted apart: voice/lines.json (v1),
voice/lines.v2.json (v2, what DIRECTION.md directs and render-elevenlabs.py renders)
and a voice:[...] array inside each showreel HTML — which is the one the film
actually speaks, through the rendered files when they exist and browser speech
synthesis when they do not, and the one build-video.js reads off
window.__UG_REEL.voiceLines.

Nothing kept them in step, so the films shipped the v1 text while every voice
document in the repo described v2. lines.v2.json is the master now and this
writes it into the films.

  sync-voice.py            rewrite every reel's voice arrays from lines.v2.json
  sync-voice.py --check    exit 1 if any reel has drifted (for CI)
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REEL_DIR = os.path.dirname(HERE)
MASTER = os.path.join(HERE, 'lines.v2.json')
REELS = ['index.html', 'sound.html', 'short.html', 'short-sound.html',
         'short-cam.html', 'short-cam-sound.html']

# A JS single-quoted string: no raw quote or backslash, or any escaped pair.
JS_STR = r"'(?:[^'\\]|\\.)*'"


def js_quote(s):
    """Quote for a JS single-quoted literal. The script carries apostrophes
    ("the no's that stay no") and em dashes, so escaping is not optional."""
    return "'" + s.replace('\\', '\\\\').replace("'", "\\'") + "'"


def master_lines():
    with open(MASTER, encoding='utf-8') as f:
        d = json.load(f)
    return {s['id']: [l['text'] for l in s['lines']] for s in d['scenes']}


def scene_spans(html):
    """Yield (scene_id, start, end) for each voice:[...] array, paired with the
    id:'...' that most recently preceded it."""
    out = []
    for m in re.finditer(r"voice:\[(" + JS_STR + r"(?:\s*,\s*" + JS_STR + r")*)\]", html):
        before = html[:m.start()]
        ids = re.findall(r"id:'(\w+)'", before)
        if not ids:
            raise SystemExit('a voice array at %d has no scene id before it' % m.start())
        out.append((ids[-1], m.start(1), m.end(1)))
    return out


def current(html, a, b):
    return [re.sub(r"\\(.)", r"\1", s[1:-1])
            for s in re.findall(JS_STR, html[a:b])]


def budget_problems(html, master_path=MASTER):
    """Both cuts share one set of lines, so a scene's real budget is the shorter
    of its long-cut duration and its compressed short-cut duration. The script
    is written to budget_seconds; if that number stops matching the film, lines
    that scan on paper get cut off mid-sentence in the reel."""
    durs = {m.group(1): float(m.group(2))
            for m in re.finditer(r"id:'(\w+)', name:'[^']*', dur:([\d.]+)", html)}
    short = {m.group(1): float(m.group(2))
             for m in re.finditer(r"\['(\w+)',([\d.]+)\]", re.search(
                 r"SHORT\s*=\s*(\[.*?\]);", html, re.S).group(1))}
    with open(master_path, encoding='utf-8') as f:
        scenes = json.load(f)['scenes']

    bad = []
    for s in scenes:
        sid, want = s['id'], float(s['budget_seconds'])
        if sid not in durs:
            bad.append('%s is in the script but not in the film' % sid)
            continue
        real = durs[sid] / short[sid] if sid in short else durs[sid]
        if abs(real - want) > 0.01:
            bad.append('%s: budget_seconds %g, but the film gives it %g s'
                       % (sid, want, round(real, 2)))
        words = sum(len(l['text'].split()) for l in s['lines'])
        # DIRECTION.md: budget near 1.8 words/second, because a pushed read is
        # what sounds robotic.
        if words / 1.8 > real:
            bad.append('%s: %d words need %.1f s at 1.8 w/s, scene is %g s'
                       % (sid, words, words / 1.8, round(real, 2)))
    return bad


def main():
    check = '--check' in sys.argv
    lines = master_lines()
    drift, wrote, timing = [], [], []

    for name in REELS:
        path = os.path.join(REEL_DIR, name)
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            html = f.read()

        spans = scene_spans(html)
        if not spans:
            raise SystemExit('%s: no voice arrays found; the reel format moved '
                             'and this tool would silently do nothing' % name)

        # the long cut carries the canonical scene durations
        if name == 'index.html':
            timing = ['%s: %s' % (name, p) for p in budget_problems(html)]

        changed = False
        # back to front, so earlier offsets stay valid
        for sid, a, b in reversed(spans):
            if sid not in lines:
                raise SystemExit('%s: scene %r is not in lines.v2.json' % (name, sid))
            want = lines[sid]
            if current(html, a, b) != want:
                drift.append('%s [%s]' % (name, sid))
                changed = True
                html = html[:a] + ','.join(js_quote(x) for x in want) + html[b:]

        if changed and not check:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(html)
            wrote.append(name)

    if timing:
        print('the script does not fit the film:')
        for t in timing:
            print('  ' + t)

    if check:
        if drift:
            print('the films do not speak the script. Drifted:')
            for d in drift:
                print('  ' + d)
            print('\nlines.v2.json is the master. Run: python3 voice/sync-voice.py')
        if drift or timing:
            return 1
        print('every reel speaks lines.v2.json, and every scene has room to say it')
        return 0

    if wrote:
        print('synced from lines.v2.json: ' + ', '.join(wrote))
        for d in drift:
            print('  ' + d)
    else:
        print('every reel already speaks lines.v2.json')
    return 1 if timing else 0


if __name__ == '__main__':
    sys.exit(main())
