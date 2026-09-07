#!/usr/bin/env bash
# Grade, camera, captions, end card, score, master — the fifteen-second cut, three shapes.
#
#   ./build.sh 16x9    frames/16x9/ + plates/16x9/ -> dist/ug-launch-ad-15s-16x9.mp4
#   ./build.sh 9x16    frames/9x16/ + plates/9x16/ -> dist/ug-launch-ad-15s-9x16.mp4
#   ./build.sh 1x1     frames/9x16/ cropped        -> dist/ug-launch-ad-15s-1x1.mp4
#
# All three carry one beat map, one camera plan, one caption schedule and one score, so
# they are the same edit at three shapes rather than three different films.
#
# The square cut crops the phone shoot, never the desktop master: the app's one-column
# mobile blocking already fits 1080 wide, so the crop only takes the frame's head and
# foot and the type inside the shot stays at phone size. Cropping the 16:9 master instead
# would put desktop-sized body copy on a phone, which is the thing a 1:1 cut exists to
# avoid.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
FFMPEG=${FFMPEG:-$(python3 -c "import imageio_ffmpeg;print(imageio_ffmpeg.get_ffmpeg_exe())" 2>/dev/null || echo ffmpeg)}
cd "$HERE"

SHAPE=${1:-16x9}
CROP=""   # only the square cut crops; 16:9 and 9:16 are shot at their delivered size
case "$SHAPE" in
  16x9) FRAMES=frames/16x9; PLATES=plates/16x9; SIZE=1920x1080 ;;
  9x16) FRAMES=frames/9x16; PLATES=plates/9x16; SIZE=1080x1920 ;;
  1x1)  FRAMES=frames/9x16; PLATES=plates/1x1;  SIZE=1080x1080; CROP="crop=1080:1080:0:420," ;;
  *)    echo "usage: build.sh 16x9|9x16|1x1" >&2; exit 2 ;;
esac
OUT="dist/ug-launch-ad-15s-$SHAPE.mp4"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT
mkdir -p dist

# --- camera. A held shot that does not move reads as a screenshot, so each long beat gets
# a ~3% push-in over its own length. The cuts reset it, so the move is always inside a shot
# and never across one. `on` is the frame number, which is why these read as beat bounds.
Z="1\
+0.020*clip((on-31)/61,0,1)*between(on,31,92)\
+0.030*clip((on-237)/53,0,1)*between(on,237,290)\
+0.030*clip((on-291)/49,0,1)*between(on,291,340)\
+0.028*clip((on-341)/42,0,1)*between(on,341,383)"

# --- captions. Burnt in, because a launch ad is watched muted in a feed. Each one sits
# over the shot it describes: the gate, the map, the compare desk, the Virtual Stage.
C0_IN=1.35; C0_OUT=3.05
C1_IN=6.15; C1_OUT=7.75
C2_IN=8.05; C2_OUT=9.60
C3_IN=9.85; C3_OUT=11.30
FD=0.28

cap () {  # $1 index  $2 in  $3 out
  local out_fade; out_fade=$(python3 -c "print(round($3-$FD,3))")
  echo "[$(( $1 + 1 )):v]format=rgba,fade=t=in:st=$2:d=$FD:alpha=1,fade=t=out:st=$out_fade:d=$FD:alpha=1[c$1];"
}

echo "== 1/4  $SHAPE  grade + camera + captions"
"$FFMPEG" -y -loglevel error \
  -framerate 30 -i "$FRAMES/%04d.png" \
  -loop 1 -t 15 -i "$PLATES/cap0.png" -loop 1 -t 15 -i "$PLATES/cap1.png" \
  -loop 1 -t 15 -i "$PLATES/cap2.png" -loop 1 -t 15 -i "$PLATES/cap3.png" \
  -filter_complex "
    [0:v]fps=30,${CROP}
      zoompan=z='$Z':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=$SIZE:fps=30,
      eq=contrast=1.06:saturation=1.08:gamma=0.99,
      vignette=PI/5,
      noise=alls=2:allf=t+u,
      format=rgba[base];
    $(cap 0 $C0_IN $C0_OUT)
    $(cap 1 $C1_IN $C1_OUT)
    $(cap 2 $C2_IN $C2_OUT)
    $(cap 3 $C3_IN $C3_OUT)
    [base][c0]overlay=0:0:enable='between(t,$C0_IN,$C0_OUT)'[o0];
    [o0][c1]overlay=0:0:enable='between(t,$C1_IN,$C1_OUT)'[o1];
    [o1][c2]overlay=0:0:enable='between(t,$C2_IN,$C2_OUT)'[o2];
    [o2][c3]overlay=0:0:enable='between(t,$C3_IN,$C3_OUT)',format=yuv420p,
      settb=1/30,fps=30[v]" \
  -map "[v]" -c:v libx264 -preset slow -crf 14 -r 30 -vsync cfr \
  -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  "$WORK/app.mp4"

echo "== 2/4  $SHAPE  end card"
# 2.20 s off one still, with a 2% settle so the card breathes rather than freezes.
"$FFMPEG" -y -loglevel error -loop 1 -t 2.2 -i "$PLATES/card.png" -filter_complex "
    [0:v]fps=30,zoompan=z='1.02-0.02*clip(on/60,0,1)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':
         d=1:s=$SIZE:fps=30,format=yuv420p,settb=1/30[v]" \
  -map "[v]" -c:v libx264 -preset slow -crf 14 -r 30 -vsync cfr -pix_fmt yuv420p \
  -colorspace bt709 -color_primaries bt709 -color_trc bt709 "$WORK/card.mp4"

echo "== 3/4  $SHAPE  dissolve"
# 15.00 s of app, 2.20 s card, a 0.50 s dissolve at 12.80 -> 15.00 s exactly.
"$FFMPEG" -y -loglevel error -i "$WORK/app.mp4" -i "$WORK/card.mp4" -filter_complex "
    [0:v]fps=30,settb=1/30[a];
    [1:v]fps=30,settb=1/30[b];
    [a][b]xfade=transition=fade:duration=0.5:offset=12.8,format=yuv420p[v]" \
  -map "[v]" -c:v libx264 -preset slow -crf 14 -r 30 -vsync cfr \
  -pix_fmt yuv420p -colorspace bt709 -color_primaries bt709 -color_trc bt709 \
  "$WORK/silent.mp4"

echo "== 4/4  $SHAPE  score"
"$FFMPEG" -y -loglevel error -i "$WORK/silent.mp4" -i audio/ug-ad-score.wav \
  -filter_complex "[1:a]atrim=0:15,asetpts=N/SR/TB,alimiter=limit=0.94:level=false,
                   aresample=48000,aformat=sample_fmts=fltp:channel_layouts=stereo[a]" \
  -map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -ar 48000 -ac 2 \
  -shortest -movflags +faststart "$OUT"

"$FFMPEG" -hide_banner -i "$OUT" 2>&1 | grep -E 'Duration|Stream'
