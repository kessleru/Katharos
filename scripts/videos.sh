#!/usr/bin/env bash
# Grava os vídeos do site com a interface de verdade (sem tela) e monta MP4 (H.264) e WebM (AV1) leves, com o pôster de cada um.
# Uso: bash scripts/videos.sh [roteiro...]   (precisa do .NET 10 e do ffmpeg). Saída em docs/video/.
set -euo pipefail
RAIZ=$(cd "$(dirname "$0")/.." && pwd)
QUADROS=${QUADROS:-$(mktemp -d)}
SAIDA="$RAIZ/docs/video"
mkdir -p "$SAIDA"
dotnet run --project "$RAIZ/app/Katharos.Fotos" -c Release -- --video "$QUADROS" "$@"
# quadro do pôster de cada vídeo (o que resume o vídeo parado)
declare -A POSTER=([tour]=0 [otimizar]=300 [raiox]=240 [aovivo]=150 [desfazer]=170)
for d in "$QUADROS"/*/; do
  n=$(basename "$d")
  ffmpeg -y -loglevel error -framerate 30 -i "$d/q%05d.png" -c:v libx264 -preset veryfast -crf 24 -pix_fmt yuv420p -movflags +faststart -an "$SAIDA/$n.mp4"
  ffmpeg -y -loglevel error -framerate 30 -i "$d/q%05d.png" -c:v libsvtav1 -preset 8 -crf 40 -pix_fmt yuv420p -svtav1-params loglevel=0 -an "$SAIDA/$n.webm" 2>/dev/null
  p=$(printf "%05d" "${POSTER[$n]:-0}")
  ffmpeg -y -loglevel error -i "$d/q$p.png" -c:v libwebp -quality 82 "$SAIDA/$n.webp"
done
ls -la "$SAIDA"
