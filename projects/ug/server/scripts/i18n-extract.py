#!/usr/bin/env python3
"""Mark every translatable static string in site/index.html and write data/i18n/en.json.

Deterministic: keys are <section>.<tag>.<slug>; running it twice changes nothing. Elements that
carry simple inline markup (<b>, <small>, <br>) get data-i18n-html and are translated as HTML with
the tags kept. Dynamic strings that the JS renders are listed in UI_KEYS and referenced with t().

Usage: python3 server/scripts/i18n-extract.py            (from projects/ug)
"""
import json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = os.path.join(ROOT, 'site', 'index.html')
OUT = os.path.join(ROOT, 'data', 'i18n')
os.makedirs(OUT, exist_ok=True)

TAGS = r'h1|h2|h3|h4|p|button|label|summary|a|span|small|div|b|li'
INLINE = r'(?:[^<]|<(?:b|small|i|br|em|strong)\b[^>]*>|</(?:b|small|i|em|strong)>)+'
PAT = re.compile(r'<(%s)\b([^>]*)>(%s)</\1>' % (TAGS, INLINE), re.S)
SKIP_IDS = {'flip', 'reachCount', 'hsTitle', 'modalTitle', 'payAmt', 'payFor', 'walletBal', 'dayTotal', 'railPillT', 'tabMeLbl', 'instHow', 'langNote', 'opsTitle', 'dockK', 'dockT', 'hint', 'tpPill', 'payStatus', 'payRef', 'railRef', 'modeLine', 'resSummary', 'wlTitle', 'wlHint', 'wlCount', 'wlLangName', 'wlHello', 'wlEchoLg', 'wlEchoSw', 'wlGo', 'wlBack', 'wlFlat', 'wlSkip', 'wlA11y', 'itinTitle', 'itinTotal', 'itinPer', 'itinNote', 'disclaimer', 'segOps'}
SKIP_TEXT = {'v1', 'v0 archived', 'MTN MoMo', 'Airtel Money', 'UG', '🎤 voice', 'night / noon', 'Plan: <b>Boujee</b>', "Today's legs: <b id=\"dayTotal\">—</b>", 'Reach · <b id="reachCount"></b>'}

# strings the JavaScript renders; keyed here so the dictionaries carry them and t() can find them
UI_KEYS = {
  'ui.bookOnUG': 'Book on UG', 'ui.sendOnUG': 'Send on UG', 'ui.takeSeat': 'Take a seat', 'ui.callAhead': 'Call ahead', 'ui.askToAdd': 'Ask UG to add it',
  'ui.tellMeWhen': 'Tell me when', 'ui.listed': 'Listed · recognised', 'ui.coming': 'Coming', 'ui.likelyCheapest': 'Likely cheapest', 'ui.cheapest': 'Cheapest',
  'ui.ugPrice': 'UG price', 'ui.ugEstimate': 'UG estimate, unverified', 'ui.min': 'min', 'ui.filling': 'Filling', 'ui.funded': 'Funded', 'ui.full': 'Full · offered to drivers',
  'ui.perSeatNow': 'per seat now', 'ui.invite': 'Invite', 'ui.accept': 'Accept', 'ui.decline': 'Decline', 'ui.atTheStage': 'At the stage', 'ui.openIn': 'or open', 'ui.directions': 'directions',
  'ui.takeEmptyLeg': 'Take the empty leg', 'ui.pointMeThere': 'Point me there', 'ui.illBeThere': "I'll be there", 'ui.signOut': 'Sign out', 'ui.copyLink': 'Copy link',
  'ui.verified': 'Verified', 'ui.pending': 'Pending', 'ui.driverAssigned': 'Driver assigned', 'ui.done': 'Done', 'ui.requested': 'Requested', 'ui.placed': 'Placed with the partner',
  'ui.arriving': 'Arriving', 'ui.onTrip': 'On trip', 'ui.trip': 'Trip', 'ui.language': 'Language', 'ui.draftNote': 'A draft; missing words show in English.',
  'ui.welcome': 'Welcome to Uganda.', 'ui.chooseLanguage': 'Choose your language', 'ui.continue': 'Continue',
  'ui.reviewNote': 'Translations were drafted by UG and checked by a second pass; native-speaker review is open. Missing words fall back to English.',
}

def slug(text, n=4):
    words = re.findall(r'[A-Za-z0-9]+', re.sub(r'<[^>]+>', '', text))
    return '_'.join(w.lower() for w in words[:n]) or 'x'

def main():
    s = open(SITE, encoding='utf-8').read()
    b0 = s.index('<body>'); b1 = s.index('<script src="https://cdnjs')
    body = s[b0:b1]
    # section id in scope for each position
    sections = [(m.start(), m.group(1)) for m in re.finditer(r'<(?:section|header|footer|nav|div class="modal"|aside)[^>]*\bid="([a-zA-Z]+)"', body)]
    def section_at(pos):
        cur = 'page'
        for p, sid in sections:
            if p <= pos: cur = sid
            else: break
        return cur
    entries = {}; used = set(); edits = []
    # the original STR keys stay authoritative for their text: an element with that exact text reuses the key
    a0 = s.index('const STR = {'); b0_ = s.index('\n};', a0)
    by_text = {}
    for m in re.finditer(r"^  ([a-zA-Z]+):\{en:(['\"])(.*?)\2", s[a0:b0_], re.M):
        by_text.setdefault(m.group(3).replace("\\'", "'"), m.group(1))
    for m in PAT.finditer(body):
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        txt = re.sub(r'\s+', ' ', inner).strip()
        plain = re.sub(r'<[^>]+>', '', txt)
        if len(plain) < 2 or re.fullmatch(r'[\d\W_]+', plain): continue
        already = re.search(r'data-i18n(-html)?="([^"]+)"', attrs)
        if already:
            k = already.group(2)
            entries[k] = {'text': txt, 'html': bool(already.group(1)), 'where': f'{section_at(m.start())} <{tag}>'}
            used.add(k)
            continue
        if re.search(r'class="[^"]*\b(mono|crest|soc|pm|q-logo)\b', attrs): continue
        idm = re.search(r'id="([^"]+)"', attrs)
        if idm and idm.group(1) in SKIP_IDS: continue
        if txt in SKIP_TEXT: continue
        if re.search(r'id="', txt): continue           # nested dynamic element
        is_html = '<' in txt
        sec = section_at(m.start())
        if not is_html and txt in by_text:
            k = by_text[txt]
            if k not in entries: entries[k] = {'text': txt, 'html': False, 'where': 'STR (nav, verbs, doors, tabs)'}
        else:
            key = f'{sec}.{tag}.{slug(plain)}'
            k = key; i = 2
            while k in used: k = f'{key}_{i}'; i += 1
            used.add(k)
            entries[k] = {'text': txt, 'html': is_html, 'where': f'{sec} <{tag}>'}
        attr = ' data-i18n-html="%s"' % k if is_html else ' data-i18n="%s"' % k
        edits.append((m.start(1) - 1, len(tag) + 1, attr))   # insert after '<tag'
    # apply edits from the end so offsets hold
    for pos, ln, attr in sorted(edits, reverse=True):
        at = pos + ln
        body = body[:at] + attr + body[at:]
    s = s[:b0] + body + s[b1:]
    open(SITE, 'w', encoding='utf-8').write(s)
    # existing STR keys stay the source of truth for their text; export them too
    a = s.index('const STR = {'); b = s.index('\n};', a)
    for m in re.finditer(r"^  ([a-zA-Z]+):\{en:(['\"])(.*?)\2", s[a:b], re.M):
        entries.setdefault(m.group(1), {'text': m.group(3).replace("\\'", "'"), 'html': False, 'where': 'STR (nav, verbs, doors, tabs)'})
    for k, v in UI_KEYS.items():
        entries.setdefault(k, {'text': v, 'html': False, 'where': 'rendered by JavaScript'})
    en = {'language': 'en', 'name': 'English', 'native': 'English', 'confidence': 'complete',
          'note': 'Source strings. Keys are section.tag.slug for page markup, bare names for the original STR keys, ui.* for strings the JavaScript renders. Values marked html keep their <b>, <small> and <br> tags in every language.',
          'strings': entries}
    with open(os.path.join(OUT, 'en.json'), 'w', encoding='utf-8') as f:
        json.dump(en, f, ensure_ascii=False, indent=1)
    print('marked', len(edits), 'elements;', len(entries), 'keys ->', os.path.relpath(os.path.join(OUT, 'en.json'), ROOT))

if __name__ == '__main__':
    main()
