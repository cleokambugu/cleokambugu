#!/usr/bin/env bash
# The six-second bumper, cut down from the same shoot.
#
# A bumper is not the fifteen for less money; it is one claim and the mark. So it keeps the
# three seconds the film actually turns on — the app answering in Luganda, the ranked
# fares, the price falling as the car fills — carries one caption instead of four, and
# gives the rest to the crest.
#
#   0.00  Tukwanirizza mu Uganda, then the whole product in Luganda   frames  96-140
#   1.53  the compare desk, cheapest first                            frames 245-290
#   3.07  the Virtual Stage                                           frames 300-340
#   4.44  the crest
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
FFMPEG=${FFMPEG:-$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())" 2>/dev/null || echo ffmpeg)}
cd "$HERE"

FRAMES=frames/16x9
PLATES=plates/16x9
OUT=dist/ug-launch-ad-6s-bumper.mp4
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
mkdir -p dist

# the two long segments push in; the opening beat is already a move, so it is left alone
Z="1+0.030*clip((on-46)/46,0,1)*between(on,46,91)+0.028*clip((on-92)/41,0,1)*between(on,92,132)"

# One caption only, over the compare desk: six seconds cannot argue three things.
C_IN=1.70; C_OUT=3.00; FD=0.22
C_OUT_FADE=$(python3 -c "print(round($C_OUT-$FD,3))")

echo "== 1/3  assemble + grade + caption"
"$FFMPEG" -y -loglevel error \
  -framerate 30 -start_number 96  -i "$FRAMES/%04d.png" \
  -framerate 30 -start_number 245 -i "$FRAMES/%04d.png" \
  -framerate 30 -start_number 300 -i "$FRAMES/%04d.png" \
  -loop 1 -t 6 -i "$PLATES/cap2.png" \
  -filter_complex "
    [0:v]trim=end_frame=45,setpts=N/30/TB[s0];
    [1:v]trim=end_frame=46,setpts=N/30/TB[s1];
    [2:v]trim=end_frame=41,setpts=N/30/TB[s2];
    [s0][s1][s2]concat=n=3:v=1:a=0,fps=30,
      zoompan=z='$Z':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1920x1080:fps=30,
      eq=contrast=1.06:saturation=1.08:gamma=0.99,
      vignette=PI/5,noise=alls=2:allf=t+u,format=rgba[base];
    [3:v]format=rgba,fade=t=in:st=$C_IN:d=$FD:alpha=1,
         fade=t=out:st=$C_OUT_FADE:d=$FD:alpha=1[c];
    [base][c]overlay=0:0:enable='between(t,$C_IN,$C_OUT)',format=yuv420p,settb=1/30,fps=30[v]" \
  -map "[v]" -c:v libx264 -preset slow -crf 14 -r 30 -vsync cfr \
  -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 "$WORK/app.mp4"

echo "== 2/3  dissolve to the card"
# 4.40 s of app, 1.90 s card, a 0.30 s dissolve at 4.10 -> 6.00 s exactly.
"$FFMPEG" -y -loglevel error -loop 1 -t 1.9 -i "$PLATES/card.png" -filter_complex "
    [0:v]fps=30,zoompan=z='1.02-0.02*clip(on/45,0,1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':
         d=1:s=1920x1080:fps=30,format=yuv420p,settb=1/30[v]" \
  -map "[v]" -c:v libx264 -preset slow -crf 14 -r 30 -vsync cfr -pix_fmt yuv420p \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 "$WORK/card.mp4"

"$FFMPEG" -y -loglevel error -i "$WORK/app.mp4" -i "$WORK/card.mp4" -filter_complex "
    [0:v]fps=30,settb=1/30[a];[1:v]fps=30,settb=1/30[b];
    [a][b]xfade=transition=fade:duration=0.3:offset=4.1,format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -preset slow -crf 14 -r 30 -vsync cfr \
  -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 "$WORK/silent.mp4"

echo "== 3/3  score"
"$FFMPEG" -y -loglevel error -i "$WORK/silent.mp4" -i audio/ug-bumper-score.wav \
  -filter_complex "[1:a]atrim=0:6,asetpts=N/SR/TB,alimiter=limit=0.94:level=false,
                   aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -shortest -movflags +faststart "$OUT"

"$FFMPEG" -hide_banner -i "$OUT" 2>&1 | grep -E 'Duration|Stream'
