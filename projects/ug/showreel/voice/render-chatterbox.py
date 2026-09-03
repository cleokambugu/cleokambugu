#!/usr/bin/env python3
"""Render the narration with Chatterbox Multilingual, cloned from a Ugandan reference voice.

This is step 3 of the cascade in CASTING.md — below recorded humans and below Sunbird's Ugandan
models, above the browser's speech synthesis. Its job is Swahili and the languages Sunbird does
not cover, spoken in a Ugandan voice rather than an American one.

Why cloning matters here: without a reference clip, Chatterbox speaks Swahili with the accent of
whoever dominates its training data. With ten seconds of a Ugandan speaker, it carries their
timbre and much of their placement across every language it supports. So the reference clip is
not a nice-to-have — it is the entire reason to use this engine rather than any other.

API read first-hand from `resemble-ai/chatterbox` (MIT), `example_tts.py` and README:

    from chatterbox.mtl_tts import ChatterboxMultilingualTTS
    model = ChatterboxMultilingualTTS.from_pretrained(device=...)
    wav = model.generate(text, language_id="sw", audio_prompt_path="ref.wav")

The README also notes that when the reference clip's language differs from the target, the output
can inherit the reference's accent, and suggests `cfg_weight=0` to reduce that. For UG that
"problem" is the point — we WANT the Ugandan reference's colour on the Swahili — so cfg_weight is
left at its default and exposed as a flag rather than forced.

    pip install chatterbox-tts torchaudio
    python3 render-chatterbox.py --ref bank/en/lead-reference.wav --langs sw,en
    python3 render-chatterbox.py --ref ... --langs sw --exaggeration 0.6

Nothing here runs in the UG sandbox: huggingface.co is blocked by the egress proxy, so the weights
cannot be fetched. Run it on a laptop or a Colab GPU. Blocked hosts are reported, not bypassed.
"""
import argparse, json, os, sys, wave, contextlib

HERE = os.path.dirname(os.path.abspath(__file__))
LINES = os.path.join(HERE, 'lines.v2.json')
OUT_ROOT = os.path.join(HERE, 'cloned')

# Chatterbox Multilingual V3 language ids, read from the repo's README language table.
SUPPORTED = {'ar','da','de','el','en','es','fi','fr','he','hi','it','ja','ko','ms','nl','no',
             'pl','pt','ru','sv','sw','tr','zh'}


def check_reference(path):
    """A short, clean, single-speaker clip is the whole quality ceiling of this method."""
    if not os.path.exists(path):
        sys.exit(f'reference clip not found: {path}\n'
                 'Record ten to twenty seconds of the lead voice reading anything, in the room '
                 'the rest of the session will use. See CASTING.md.')
    try:
        with contextlib.closing(wave.open(path)) as w:
            secs = w.getnframes() / float(w.getframerate())
            if secs < 6:
                print(f'  warning: reference is {secs:.1f}s. Ten seconds or more clones better.')
            if secs > 40:
                print(f'  warning: reference is {secs:.1f}s. Long clips add room, not identity; trim to ~15s.')
            if w.getnchannels() != 1:
                print('  warning: reference is not mono. Chatterbox is happier with mono.')
    except wave.Error:
        print('  note: could not read the reference as WAV; passing it through anyway.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', required=True, help='10-20s WAV of the Ugandan reference voice')
    ap.add_argument('--langs', default='sw', help='comma-separated language ids to render')
    ap.add_argument('--exaggeration', type=float, default=0.5,
                    help='0.3 flat and factual, 0.5 neutral, 0.7 warm. The narration wants 0.45-0.55.')
    ap.add_argument('--cfg-weight', type=float, default=None,
                    help='leave unset to keep the reference accent, which is the point; 0 to suppress it')
    ap.add_argument('--dry-run', action='store_true', help='report what would be rendered and stop')
    args = ap.parse_args()

    langs = [l.strip() for l in args.langs.split(',') if l.strip()]
    bad = [l for l in langs if l not in SUPPORTED]
    if bad:
        sys.exit(f'Chatterbox does not speak: {", ".join(bad)}.\n'
                 'Its 23 languages carry exactly one African language, Swahili. For Luganda, Ateso, '
                 'Lugbara, Acholi, Runyankore and the rest, use render.py (Sunbird SALT) — see '
                 'ENGINES.md for why no other open model covers them.')

    with open(LINES, encoding='utf-8') as fh:
        script = json.load(fh)
    scenes = script['scenes'] if isinstance(script, dict) and 'scenes' in script else script

    check_reference(args.ref)
    total = sum(len(sc.get('lines', sc.get('voice', []))) for sc in scenes)
    print(f'{total} lines x {len(langs)} language(s) from {os.path.basename(LINES)}')
    if args.dry_run:
        for sc in scenes:
            for i, line in enumerate(sc.get('lines', sc.get('voice', []))):
                text = line['text'] if isinstance(line, dict) else line
                print(f"  {sc.get('id','?')}-{i+1}: {str(text)[:72]}")
        return

    from chatterbox.mtl_tts import ChatterboxMultilingualTTS   # noqa: E402
    import torch, torchaudio as ta                             # noqa: E402

    device = 'cuda' if torch.cuda.is_available() else ('mps' if torch.backends.mps.is_available() else 'cpu')
    print(f'device: {device}')
    model = ChatterboxMultilingualTTS.from_pretrained(device=device)

    manifest = {'engine': 'resemble-ai/chatterbox multilingual v3',
                'reference': os.path.basename(args.ref), 'scenes': []}

    for lang in langs:
        out_dir = os.path.join(OUT_ROOT, lang)
        os.makedirs(out_dir, exist_ok=True)
        for sc in scenes:
            sid = sc.get('id', 'scene')
            files = []
            for i, line in enumerate(sc.get('lines', sc.get('voice', []))):
                text = line['text'] if isinstance(line, dict) else line
                text = text.get(lang, text.get('en')) if isinstance(text, dict) else text
                kw = dict(language_id=lang, audio_prompt_path=args.ref, exaggeration=args.exaggeration)
                if args.cfg_weight is not None:
                    kw['cfg_weight'] = args.cfg_weight
                wav = model.generate(text, **kw)
                name = f'{sid}-{i+1}.wav'
                ta.save(os.path.join(out_dir, name), wav, model.sr)
                files.append({'file': f'{lang}/{name}', 'text': text})
                print(f'  {lang}/{name}')
            manifest['scenes'].append({'id': sid, 'lang': lang, 'files': files})

    with open(os.path.join(OUT_ROOT, 'manifest.json'), 'w', encoding='utf-8') as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=2)
    print(f'\nwrote {OUT_ROOT}/manifest.json')
    print('The reel plays bank/ first, then rendered/, then this. It says on screen which one it '
          'is using, so a cloned take is never passed off as a person.')


if __name__ == '__main__':
    main()
