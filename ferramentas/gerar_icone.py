"""Gera assets/icone.ico (usado no executável).

Rode com: python ferramentas/gerar_icone.py
"""
import struct
from pathlib import Path

import cv2
import numpy as np

TAMANHOS = (16, 32, 48, 64, 128, 256)
BASE = 1024
DESTINO = Path(__file__).resolve().parent.parent / "assets" / "icone.ico"

AZUL = (255, 128, 0, 255)      # B, G, R, A
VERDE = (60, 200, 60, 255)
VERMELHO = (50, 50, 230, 255)
AMARELO = (40, 220, 250, 255)
ESCURO = (45, 45, 45, 255)
BRANCO = (255, 255, 255, 255)


def retangulo_arredondado(img, x1, y1, x2, y2, raio, cor):
    cv2.rectangle(img, (x1 + raio, y1), (x2 - raio, y2), cor, -1, cv2.LINE_AA)
    cv2.rectangle(img, (x1, y1 + raio), (x2, y2 - raio), cor, -1, cv2.LINE_AA)
    for cx, cy in ((x1 + raio, y1 + raio), (x2 - raio, y1 + raio),
                   (x1 + raio, y2 - raio), (x2 - raio, y2 - raio)):
        cv2.circle(img, (cx, cy), raio, cor, -1, cv2.LINE_AA)


def desenhar(tamanho):
    img = np.zeros((tamanho, tamanho, 4), dtype=np.uint8)
    margem = int(tamanho * 0.05)
    raio = int(tamanho * 0.20)
    x1, y1 = margem, margem
    x2, y2 = tamanho - margem, tamanho - margem

    # Fundo branco com borda escura
    retangulo_arredondado(img, x1, y1, x2, y2, raio, ESCURO)
    borda = max(1, int(tamanho * 0.045))
    retangulo_arredondado(img, x1 + borda, y1 + borda, x2 - borda,
                          y2 - borda, max(1, raio - borda), BRANCO)

    # Traços coloridos (o "desenho no ar")
    espessura = max(2, int(tamanho * 0.085))
    pontos = [
        (int(tamanho * 0.22), int(tamanho * 0.68)),
        (int(tamanho * 0.38), int(tamanho * 0.43)),
        (int(tamanho * 0.52), int(tamanho * 0.60)),
        (int(tamanho * 0.67), int(tamanho * 0.35)),
        (int(tamanho * 0.80), int(tamanho * 0.55)),
    ]
    cores = (AZUL, VERDE, VERMELHO, AMARELO)
    for i in range(len(pontos) - 1):
        cv2.line(img, pontos[i], pontos[i + 1], cores[i % len(cores)],
                 espessura, cv2.LINE_AA)

    # Ponta da "caneta"
    cv2.circle(img, pontos[-1], espessura, AMARELO, -1, cv2.LINE_AA)
    cv2.circle(img, pontos[-1], max(1, espessura // 3), ESCURO, -1,
               cv2.LINE_AA)
    return img


def escrever_ico(caminho, imagens):
    entradas = []
    dados = b""
    offset = 6 + 16 * len(imagens)
    for tamanho, bgra in imagens:
        cabecalho = struct.pack("<IiiHHIIiiII", 40, tamanho, tamanho * 2, 1,
                                32, 0, 0, 0, 0, 0, 0)
        xor = bgra[::-1].tobytes()  # linhas de baixo para cima
        linha_and = ((tamanho + 31) // 32) * 4
        and_mask = b"\x00" * (linha_and * tamanho)
        payload = cabecalho + xor + and_mask
        entradas.append(struct.pack("<BBBBHHII", tamanho % 256, tamanho % 256,
                                    0, 0, 1, 32, len(payload), offset))
        dados += payload
        offset += len(payload)

    with open(caminho, "wb") as arquivo:
        arquivo.write(struct.pack("<HHH", 0, 1, len(imagens)))
        arquivo.write(b"".join(entradas))
        arquivo.write(dados)


def main():
    base = desenhar(BASE)
    imagens = []
    for tamanho in TAMANHOS:
        redimensionada = cv2.resize(base, (tamanho, tamanho),
                                    interpolation=cv2.INTER_AREA)
        imagens.append((tamanho, redimensionada))
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    escrever_ico(DESTINO, imagens)
    print(f"Ícone gerado em {DESTINO}")


if __name__ == "__main__":
    main()
