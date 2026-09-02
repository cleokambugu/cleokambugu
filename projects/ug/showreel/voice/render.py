#!/usr/bin/env python3
"""Render the UG showreel narration with Ugandan voices.

Engine: Sunbird AI's Spark-TTS SALT (``Sunbird/spark-tts-salt`` on Hugging Face), a 0.5B
text-to-speech model fine-tuned on the SALT studio corpus for Acholi, Ateso, Luganda, Lugbara,
Runyankore, Swahili and Ugandan-accented English. The prompt format and the detokenise step
below follow ``notebooks/evaluation/spark-tts-inference-example.ipynb`` in the SunbirdAI/salt
repository, read first-hand. Speaker ids are the ones listed in that notebook; add or change
them in ``lines.json`` per line.

Usage
  python render.py --check                 # validate lines.json against sound.html, no model
  python render.py --dry-run               # print what would render
  python render.py                         # render voice/*.wav and voice/manifest.json
  python render.py --device cpu            # slow but works without a GPU (minutes per line)

Needs network access to huggingface.co (and GitHub for the Spark-TTS codec); this sandbox's
egress proxy blocks both, so run it on a laptop or a Colab GPU. Install:
  pip install -U transformers torch torchaudio soundfile huggingface_hub omegaconf einx einops
  git clone https://github.com/SparkAudio/Spark-TTS   # BiCodec tokenizer

The showreel (``sound.html``) fetches ``voice/manifest.json`` at start; if it is present it plays
these files, otherwise it falls back to the browser's speech synthesis and says so on screen.
"""
import argparse, json, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
LINES = os.path.join(HERE, 'lines.json')
REEL = os.path.join(HERE, '..', 'sound.html')
MODEL = os.environ.get('UG_TTS_MODEL', 'Sunbird/spark-tts-salt')
CODEC = os.environ.get('UG_TTS_CODEC', 'unsloth/Spark-TTS-0.5B')


def load_lines():
    with open(LINES, encoding='utf-8') as f:
        data = json.load(f)
    assert isinstance(data.get('scenes'), list), 'lines.json needs a scenes list'
    spk = data.get('speakers', {})
    for sc in data['scenes']:
        assert sc.get('id') and isinstance(sc.get('lines'), list), f'bad scene {sc}'
        for ln in sc['lines']:
            assert ln.get('text'), f'line needs text: {ln}'
            lang = ln.setdefault('lang', 'en')
            ln['speaker'] = ln.get('speaker') or (spk.get(lang) or {}).get('id')
    return data


def require_speakers(data):
    missing = sorted({ln['lang'] for sc in data['scenes'] for ln in sc['lines'] if not ln['speaker']})
    if missing:
        sys.exit(f"no speaker id for {missing}: set speakers.<lang>.id in lines.json (see the model card)")


def check(data):
    """The fallback text in sound.html must match lines.json, so both cuts say the same thing."""
    src = open(REEL, encoding='utf-8').read()
    ids = re.findall(r"^\{ id:'([a-z]+)'", src, re.M)
    ok = True
    for sc in data['scenes']:
        if sc['id'] not in ids:
            print('scene not in sound.html:', sc['id']); ok = False
        for ln in sc['lines']:
            if ln['text'] not in src:
                print('line not in sound.html:', ln['text']); ok = False
    print('lines.json:', len(data['scenes']), 'scenes,', sum(len(s['lines']) for s in data['scenes']), 'lines,', 'ok' if ok else 'MISMATCH')
    return ok


def render(data, device, out_dir):
    import numpy as np, torch, transformers, soundfile as sf
    from huggingface_hub import snapshot_download
    sys.path.append(os.path.join(HERE, 'Spark-TTS'))
    from sparktts.models.audio_tokenizer import BiCodecTokenizer
    snapshot_download(CODEC, local_dir=os.path.join(HERE, 'Spark-TTS-0.5B'), ignore_patterns=['*LLM*'])
    codec = BiCodecTokenizer(os.path.join(HERE, 'Spark-TTS-0.5B'), device)
    model = transformers.AutoModelForCausalLM.from_pretrained(MODEL, device_map=device, torch_dtype='auto')
    tok = transformers.AutoTokenizer.from_pretrained(MODEL)
    manifest = {'engine': MODEL, 'rate': 16000, 'scenes': []}
    for sc in data['scenes']:
        files = []
        for i, ln in enumerate(sc['lines']):
            text = f"{ln['speaker']}: {ln['text']}"
            prompt = '<|task_tts|><|start_content|>' + text + '<|end_content|><|start_global_token|>'
            inp = tok([prompt], return_tensors='pt').to(device)
            t0 = time.time()
            with torch.inference_mode():
                gen = model.generate(**inp, max_new_tokens=2048, do_sample=True, temperature=0.8, top_k=50, top_p=1,
                                     eos_token_id=tok.eos_token_id, pad_token_id=tok.pad_token_id)
            out = tok.batch_decode(gen[:, inp.input_ids.shape[1]:], skip_special_tokens=False)[0]
            sem = torch.tensor([int(x) for x in re.findall(r'bicodec_semantic_(\d+)', out)]).long().unsqueeze(0)
            glo = torch.tensor([int(x) for x in re.findall(r'bicodec_global_(\d+)', out)]).long().unsqueeze(0).unsqueeze(0)
            wav = codec.detokenize(glo.to(device).squeeze(0), sem.to(device))
            name = f"{sc['id']}-{i+1}.wav"
            sf.write(os.path.join(out_dir, name), np.asarray(wav), 16000)
            files.append({'file': name, 'text': ln['text'], 'lang': ln.get('lang', 'en'), 'speaker': ln['speaker'], 'seconds': round(len(wav) / 16000, 2)})
            print(f'{name}  {time.time()-t0:.1f}s  {ln["text"][:60]}')
        manifest['scenes'].append({'id': sc['id'], 'files': files})
    with open(os.path.join(out_dir, 'manifest.json'), 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
    print('wrote manifest.json')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--device', default='cuda')
    ap.add_argument('--out', default=HERE)
    a = ap.parse_args()
    data = load_lines()
    if a.check:
        sys.exit(0 if check(data) else 1)
    if a.dry_run:
        for sc in data['scenes']:
            for i, ln in enumerate(sc['lines']):
                print(f"{sc['id']}-{i+1}.wav  [{ln['lang']} speaker {ln['speaker'] or '?'}]  {ln['text']}")
        return
    require_speakers(data)
    render(data, a.device, a.out)


if __name__ == '__main__':
    main()
