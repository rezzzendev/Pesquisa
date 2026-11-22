#!/bin/bash
# rodar_vosviewer.sh - Abre cada rede gerada por gerar_redes.py no VOSviewer,
# roda layout + clustering (VOS, normalizacao association strength - padrao),
# salva o mapa final (map/network/json) e exporta imagens PNG.
#
# Uso: bash analise/rodar_vosviewer.sh [caminho/VOSviewer.jar]
set -u
JAR="${1:-$HOME/.local/opt/VOSviewer/VOSviewer.jar}"
BASE="$(cd "$(dirname "$0")/.." && pwd)"
IN="$BASE/resultados/vosviewer"
OUT="$BASE/resultados/mapas"
IMG="$BASE/resultados/imagens"
mkdir -p "$OUT" "$IMG"

roda() {  # roda <nome> <png_final> [parametros extras do VOSviewer...]
  local nome="$1" png="$2"; shift 2
  rm -f "$png"
  java -Xmx4g -jar "$JAR" \
    -map "$IN/${nome}_map.txt" -network "$IN/${nome}_network.txt" \
    -file_location "$OUT" -white_background true "$@" \
    -save_screenshot_png "$png" >/dev/null 2>&1 &
  local pid=$!
  for _ in $(seq 1 180); do            # espera ate 3 min pela imagem
    [ -s "$png" ] && { sleep 3; break; }
    sleep 1
  done
  kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
  if [ -s "$png" ]; then echo "ok  $(basename "$png")"; else echo "FALHOU  $nome"; fi
}

for nome in palavras_chave cocitacao_refs paises cocitacao_fontes; do
  # 1a passada: calcula layout/clusters, salva o mapa pronto e a visao de rede
  roda "$nome" "$IMG/${nome}_rede.png" -run_layout -run_clustering \
       -save_map "$OUT/${nome}_map.txt" -save_network "$OUT/${nome}_network.txt" \
       -save_json "$OUT/${nome}.json" -network_visualization
done

# Visualizacoes extras a partir do mapa ja calculado (mesmas posicoes/cores)
abre() { local nome="$1" png="$2"; shift 2
  IN="$OUT" roda_saved "$nome" "$png" "$@"; }
roda_saved() {
  local nome="$1" png="$2"; shift 2
  rm -f "$png"
  java -Xmx4g -jar "$JAR" -map "$OUT/${nome}_map.txt" -network "$OUT/${nome}_network.txt" \
    -white_background true "$@" -save_screenshot_png "$png" >/dev/null 2>&1 &
  local pid=$!
  for _ in $(seq 1 120); do [ -s "$png" ] && { sleep 3; break; }; sleep 1; done
  kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
  if [ -s "$png" ]; then echo "ok  $(basename "$png")"; else echo "FALHOU  $nome (extra)"; fi
}
roda_saved palavras_chave "$IMG/palavras_chave_overlay_ano.png" -overlay_visualization
roda_saved palavras_chave "$IMG/palavras_chave_densidade.png" -density_visualization
roda_saved paises        "$IMG/paises_densidade.png" -density_visualization
