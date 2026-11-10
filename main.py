import os
import sys
import time
from pathlib import Path

import cv2
import numpy as np

# Em executáveis "sem console" (PyInstaller --windowed), stdout/stderr são None.
# Redirecionar para o "nada" evita erros ao usar print().
if sys.stdout is None:
    sys.stdout = open(os.devnull, "w", encoding="utf-8")
if sys.stderr is None:
    sys.stderr = open(os.devnull, "w", encoding="utf-8")

LARGURA, ALTURA = 640, 480

# Cores em BGR (padrão do OpenCV)
AZUL = (255, 0, 0)
VERDE = (0, 255, 0)
VERMELHO = (0, 0, 255)
AMARELO = (0, 255, 255)

# Botões: (nome, x1, x2, cor)
BOTOES = [
    ("CLEAR ALL", 40, 140, (122, 122, 122)),
    ("BLUE", 160, 255, AZUL),
    ("GREEN", 275, 370, VERDE),
    ("RED", 390, 485, VERMELHO),
    ("YELLOW", 505, 600, AMARELO),
]
BOTAO_Y2 = 65

ESPESSURA = 4
AREA_MINIMA = 500  # ignora ruídos pequenos na máscara

# Limites HSV iniciais (tons de azul). Ajuste nos sliders para a cor do seu objeto.
LIMITE_INFERIOR_PADRAO = (64, 72, 49)
LIMITE_SUPERIOR_PADRAO = (153, 255, 255)

# Tamanho das janelas na tela: 1.0 = 640x480, 1.5 = 960x720, 2.0 = 1280x960
ESCALA_EXIBICAO = 1.0
ESCALA_MASK = 0.5  # janela "mask" é só diagnóstico, fica menor

JANELA_TRACKING = "Tracking"
JANELA_PAINT = "Paint"
JANELA_MASCARA = "mask"
JANELA_CORES = "Color detectors"


def ampliar(img, escala=None):
    """Aumenta a imagem só para exibir (o desenho continua em 640x480)."""
    escala = ESCALA_EXIBICAO if escala is None else escala
    if escala == 1.0:
        return img
    interp = cv2.INTER_AREA if escala < 1 else cv2.INTER_CUBIC
    return cv2.resize(img, None, fx=escala, fy=escala, interpolation=interp)


def nada(_):
    pass


def mostrar_erro(titulo, mensagem):
    """Mostra um aviso mesmo quando o programa roda sem console (exe)."""
    print(f"{titulo}: {mensagem}")
    try:
        import ctypes

        # MB_OK | MB_ICONERROR
        ctypes.windll.user32.MessageBoxW(None, mensagem, titulo, 0x00000010)
    except Exception:
        pass


def abrir_camera():
    """Tenta abrir a webcam com os backends/índices mais comuns do Windows."""
    tentativas = [
        (0, None),
        (0, cv2.CAP_DSHOW),
        (1, None),
        (1, cv2.CAP_DSHOW),
    ]
    for indice, backend in tentativas:
        cap = (cv2.VideoCapture(indice) if backend is None
               else cv2.VideoCapture(indice, backend))
        if cap.isOpened():
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, LARGURA)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTURA)
            print(f"Webcam aberta (índice {indice}, backend {backend}).")
            return cap
        cap.release()
    return None


def criar_trackbars():
    """Janela com sliders para ajustar a cor rastreada em tempo real."""
    cv2.namedWindow(JANELA_CORES, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(JANELA_CORES, 360, 230)
    lh, ls, lv = LIMITE_INFERIOR_PADRAO
    uh, us, uv = LIMITE_SUPERIOR_PADRAO
    cv2.createTrackbar("Upper Hue", JANELA_CORES, uh, 180, nada)
    cv2.createTrackbar("Upper Saturation", JANELA_CORES, us, 255, nada)
    cv2.createTrackbar("Upper Value", JANELA_CORES, uv, 255, nada)
    cv2.createTrackbar("Lower Hue", JANELA_CORES, lh, 180, nada)
    cv2.createTrackbar("Lower Saturation", JANELA_CORES, ls, 255, nada)
    cv2.createTrackbar("Lower Value", JANELA_CORES, lv, 255, nada)


def ler_limites_hsv():
    uh = cv2.getTrackbarPos("Upper Hue", JANELA_CORES)
    us = cv2.getTrackbarPos("Upper Saturation", JANELA_CORES)
    uv = cv2.getTrackbarPos("Upper Value", JANELA_CORES)
    lh = cv2.getTrackbarPos("Lower Hue", JANELA_CORES)
    ls = cv2.getTrackbarPos("Lower Saturation", JANELA_CORES)
    lv = cv2.getTrackbarPos("Lower Value", JANELA_CORES)
    return np.array([lh, ls, lv]), np.array([uh, us, uv])


def desenhar_botoes(img):
    for nome, x1, x2, cor in BOTOES:
        cv2.rectangle(img, (x1, 1), (x2, BOTAO_Y2), cor, -1)
        # texto branco (preto no amarelo para ler melhor)
        cor_texto = (0, 0, 0) if nome == "YELLOW" else (255, 255, 255)
        cv2.putText(img, nome, (x1 + 8, 42), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, cor_texto, 2, cv2.LINE_AA)


def encontrar_ponta(mascara):
    """Retorna (x, y, raio) do maior contorno, ou None se não achar nada."""
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
    if not contornos:
        return None
    maior = max(contornos, key=cv2.contourArea)
    if cv2.contourArea(maior) < AREA_MINIMA:
        return None
    (x, y), raio = cv2.minEnclosingCircle(maior)
    return int(x), int(y), int(raio)


def desenhar_aviso(img, texto):
    """Escreve um aviso no rodapé da imagem."""
    if not texto:
        return
    fonte = cv2.FONT_HERSHEY_SIMPLEX
    escala = 0.55
    (tw, th), _ = cv2.getTextSize(texto, fonte, escala, 2)
    x, y = 12, ALTURA - 12
    cv2.rectangle(img, (x - 8, y - th - 10), (x + tw + 8, y + 8),
                  (40, 40, 40), -1)
    cv2.putText(img, texto, (x, y), fonte, escala, (255, 255, 255), 2,
                cv2.LINE_AA)


def pasta_salvamento():
    """Escolhe uma pasta onde o usuário realmente pode gravar o PNG."""
    candidatos = []
    if os.name == "nt":
        candidatos.append(Path.home() / "Pictures" / "DesenhoNaTela")
    candidatos.append(Path.home() / "DesenhoNaTela")
    candidatos.append(Path.cwd())
    for pasta in candidatos:
        try:
            pasta.mkdir(parents=True, exist_ok=True)
            teste = pasta / ".teste_escrita"
            teste.write_bytes(b"")
            teste.unlink()
            return pasta
        except OSError:
            continue
    return Path.cwd()


def salvar_desenho(tela):
    """Salva o desenho em PNG e devolve o caminho (ou None em caso de erro)."""
    pasta = pasta_salvamento()
    caminho = pasta / "desenho.png"
    try:
        # imencode + write_bytes funciona com caminhos acentuados no Windows.
        ok, buffer = cv2.imencode(".png", tela)
        if not ok:
            raise OSError("não foi possível codificar a imagem")
        caminho.write_bytes(buffer.tobytes())
        print(f"Desenho salvo em {caminho}")
        return caminho
    except OSError as exc:
        print(f"Falha ao salvar o desenho: {exc}")
        return None


def janela_aberta(nome):
    try:
        return cv2.getWindowProperty(nome, cv2.WND_PROP_VISIBLE) >= 1
    except cv2.error:
        return False


def organizar_janelas():
    """Posiciona as janelas lado a lado para não ficarem uma em cima da outra."""
    largura_janela = int(LARGURA * ESCALA_EXIBICAO)
    altura_janela = int(ALTURA * ESCALA_EXIBICAO)
    cv2.moveWindow(JANELA_TRACKING, 20, 20)
    cv2.moveWindow(JANELA_PAINT, 20 + largura_janela + 20, 20)
    cv2.moveWindow(JANELA_CORES, 20, 20 + altura_janela + 30)
    cv2.moveWindow(JANELA_MASCARA, 20 + largura_janela + 20,
                   20 + altura_janela + 30)


def alternar_tela_cheia():
    try:
        cheia = cv2.getWindowProperty(
            JANELA_PAINT, cv2.WND_PROP_FULLSCREEN) == cv2.WINDOW_FULLSCREEN
        cv2.setWindowProperty(JANELA_PAINT, cv2.WND_PROP_FULLSCREEN,
                              cv2.WINDOW_NORMAL if cheia
                              else cv2.WINDOW_FULLSCREEN)
    except cv2.error:
        pass


def autoteste():
    """Teste rápido sem webcam, usado para validar o executável."""
    frame = np.full((ALTURA, LARGURA, 3), 255, dtype=np.uint8)
    cv2.circle(frame, (320, 240), 25, AZUL, -1)

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mascara = cv2.inRange(hsv, np.array(LIMITE_INFERIOR_PADRAO),
                          np.array(LIMITE_SUPERIOR_PADRAO))
    kernel = np.ones((5, 5), np.uint8)
    mascara = cv2.erode(mascara, kernel, iterations=1)
    mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)
    mascara = cv2.dilate(mascara, kernel, iterations=1)

    ponta = encontrar_ponta(mascara)
    if ponta is None:
        raise RuntimeError("máscara não encontrou o objeto de teste")
    x, y, _ = ponta
    if abs(x - 320) > 5 or abs(y - 240) > 5:
        raise RuntimeError(f"ponta fora do esperado: {(x, y)}")

    tela = np.full((ALTURA, LARGURA, 3), 255, dtype=np.uint8)
    desenhar_botoes(tela)
    cv2.line(tela, (100, 200), (500, 400), AZUL, ESPESSURA)
    if not np.any(tela != 255):
        raise RuntimeError("nada foi desenhado na tela")
    return True


def main():
    cap = abrir_camera()
    if cap is None:
        mostrar_erro(
            "Desenho na Tela",
            "Não foi possível abrir a webcam.\n\n"
            "Verifique se:\n"
            "- a webcam está conectada e não está em uso por outro programa;\n"
            "- o acesso à câmera está permitido nas configurações do Windows\n"
            "  (Privacidade e segurança > Câmera).",
        )
        return 1

    tela = np.full((ALTURA, LARGURA, 3), 255, dtype=np.uint8)  # canvas branco
    cor_atual = AZUL
    ponto_anterior = None
    kernel = np.ones((5, 5), np.uint8)
    mostrar_mascara = True
    janelas_posicionadas = False
    falhas_consecutivas = 0
    aviso = ""
    aviso_expira = 0.0

    try:
        criar_trackbars()

        while True:
            ok, frame = cap.read()
            if not ok or frame is None:
                falhas_consecutivas += 1
                if falhas_consecutivas > 30:
                    mostrar_erro("Desenho na Tela",
                                 "A webcam parou de enviar imagens.")
                    break
                time.sleep(0.05)
                continue
            falhas_consecutivas = 0

            frame = cv2.flip(frame, 1)  # efeito espelho
            frame = cv2.resize(frame, (LARGURA, ALTURA))

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            inferior, superior = ler_limites_hsv()

            mascara = cv2.inRange(hsv, inferior, superior)
            mascara = cv2.erode(mascara, kernel, iterations=1)
            mascara = cv2.morphologyEx(mascara, cv2.MORPH_OPEN, kernel)
            mascara = cv2.dilate(mascara, kernel, iterations=1)

            ponta = encontrar_ponta(mascara)

            if ponta is not None:
                x, y, raio = ponta
                cv2.circle(frame, (x, y), raio, AMARELO, 2)  # círculo no objeto
                cv2.circle(frame, (x, y), 4, (0, 0, 0), -1)

                if y <= BOTAO_Y2:
                    # Ponta está na área dos botões: trocar cor / limpar
                    ponto_anterior = None
                    for nome, x1, x2, cor in BOTOES:
                        if x1 <= x <= x2:
                            if nome == "CLEAR ALL":
                                tela[:] = 255
                            else:
                                cor_atual = cor
                else:
                    # Desenhando
                    if ponto_anterior is not None:
                        cv2.line(tela, ponto_anterior, (x, y), cor_atual,
                                 ESPESSURA)
                        cv2.line(frame, ponto_anterior, (x, y), cor_atual,
                                 ESPESSURA)
                    ponto_anterior = (x, y)
            else:
                ponto_anterior = None  # "levantou a caneta"

            # Mostra o desenho também por cima da imagem da câmera
            riscos = cv2.cvtColor(tela, cv2.COLOR_BGR2GRAY) < 250
            frame[riscos] = tela[riscos]

            desenhar_botoes(frame)
            tela_visivel = tela.copy()
            desenhar_botoes(tela_visivel)

            if aviso and time.time() < aviso_expira:
                desenhar_aviso(frame, aviso)
                desenhar_aviso(tela_visivel, aviso)

            cv2.imshow(JANELA_TRACKING, ampliar(frame))
            cv2.imshow(JANELA_PAINT, ampliar(tela_visivel))
            if mostrar_mascara:
                cv2.imshow(JANELA_MASCARA, ampliar(mascara, ESCALA_MASK))

            if not janelas_posicionadas:
                organizar_janelas()
                janelas_posicionadas = True

            # Fechar a janela no "X" também encerra o programa
            if not janela_aberta(JANELA_TRACKING) or \
                    not janela_aberta(JANELA_CORES):
                break

            tecla = cv2.waitKey(1) & 0xFF
            if tecla in (ord("q"), 27):  # q ou ESC
                break
            elif tecla == ord("c"):
                tela[:] = 255
                aviso, aviso_expira = "Tela limpa", time.time() + 1.5
            elif tecla == ord("f"):
                alternar_tela_cheia()
            elif tecla == ord("m"):
                mostrar_mascara = not mostrar_mascara
                if not mostrar_mascara:
                    cv2.destroyWindow(JANELA_MASCARA)
            elif tecla == ord("s"):
                caminho = salvar_desenho(tela)
                if caminho is None:
                    aviso = "Erro ao salvar o desenho"
                else:
                    aviso = f"Desenho salvo: {caminho.name}"
                aviso_expira = time.time() + 3.0
    except cv2.error as exc:
        mostrar_erro("Desenho na Tela", f"Erro do OpenCV:\n{exc}")
        return 1
    finally:
        cap.release()
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass
    return 0


if __name__ == "__main__":
    if "--autoteste" in sys.argv:
        try:
            autoteste()
            sys.exit(0)
        except Exception as exc:  # noqa: BLE001 - teste precisa de código de saída
            print(f"Autoteste falhou: {exc}")
            sys.exit(1)
    sys.exit(main())
