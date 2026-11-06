
import cv2
import numpy as np

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

# Tamanho das janelas na tela: 1.0 = 640x480, 1.5 = 960x720, 2.0 = 1280x960
ESCALA_EXIBICAO = 2.0
ESCALA_MASK = 1.0  # janela "mask" é só diagnóstico, fica menor


def ampliar(img, escala=None):
    """Aumenta a imagem só para exibir (o desenho continua em 640x480)."""
    escala = ESCALA_EXIBICAO if escala is None else escala
    if escala == 1.0:
        return img
    interp = cv2.INTER_AREA if escala < 1 else cv2.INTER_CUBIC
    return cv2.resize(img, None, fx=escala, fy=escala, interpolation=interp)


def nada(_):
    pass


def criar_trackbars():
    """Janela com sliders para ajustar a cor rastreada em tempo real."""
    cv2.namedWindow("Color detectors")
    cv2.resizeWindow("Color detectors", 400, 300)
    # Valores iniciais: tons de azul. Ajuste para a cor do seu objeto.
    cv2.createTrackbar("Upper Hue", "Color detectors", 153, 180, nada)
    cv2.createTrackbar("Upper Saturation", "Color detectors", 255, 255, nada)
    cv2.createTrackbar("Upper Value", "Color detectors", 255, 255, nada)
    cv2.createTrackbar("Lower Hue", "Color detectors", 64, 180, nada)
    cv2.createTrackbar("Lower Saturation", "Color detectors", 72, 255, nada)
    cv2.createTrackbar("Lower Value", "Color detectors", 49, 255, nada)


def ler_limites_hsv():
    uh = cv2.getTrackbarPos("Upper Hue", "Color detectors")
    us = cv2.getTrackbarPos("Upper Saturation", "Color detectors")
    uv = cv2.getTrackbarPos("Upper Value", "Color detectors")
    lh = cv2.getTrackbarPos("Lower Hue", "Color detectors")
    ls = cv2.getTrackbarPos("Lower Saturation", "Color detectors")
    lv = cv2.getTrackbarPos("Lower Value", "Color detectors")
    return np.array([lh, ls, lv]), np.array([uh, us, uv])


def desenhar_botoes(img):
    for nome, x1, x2, cor in BOTOES:
        cv2.rectangle(img, (x1, 1), (x2, BOTAO_Y2), cor, -1)
        # texto branco (preto no amarelo para ler melhor)
        cor_texto = (0, 0, 0) if nome == "YELLOW" else (255, 255, 255)
        cv2.putText(img, nome, (x1 + 8, 42), cv2.FONT_HERSHEY_SIMPLEX,
                    0.55, cor_texto, 2, cv2.LINE_AA)


def encontrar_ponta(mascara):
    """Retorna (x, y) do centro do maior contorno, ou None se não achar nada."""
    contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)
    if not contornos:
        return None
    maior = max(contornos, key=cv2.contourArea)
    if cv2.contourArea(maior) < AREA_MINIMA:
        return None
    (x, y), raio = cv2.minEnclosingCircle(maior)
    return int(x), int(y), int(raio)


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Não foi possível abrir a webcam.")
        return
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, LARGURA)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, ALTURA)

    criar_trackbars()

    tela = np.full((ALTURA, LARGURA, 3), 255, dtype=np.uint8)  # canvas branco
    cor_atual = AZUL
    ponto_anterior = None
    kernel = np.ones((5, 5), np.uint8)

    while True:
        ok, frame = cap.read()
        if not ok:
            break
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
                    cv2.line(tela, ponto_anterior, (x, y), cor_atual, ESPESSURA)
                    cv2.line(frame, ponto_anterior, (x, y), cor_atual, ESPESSURA)
                ponto_anterior = (x, y)
        else:
            ponto_anterior = None  # "levantou a caneta"

        # Mostra o desenho também por cima da imagem da câmera
        riscos = cv2.cvtColor(tela, cv2.COLOR_BGR2GRAY) < 250
        frame[riscos] = tela[riscos]

        desenhar_botoes(frame)
        tela_visivel = tela.copy()
        desenhar_botoes(tela_visivel)

        cv2.imshow("Tracking", ampliar(frame))
        cv2.imshow("Paint", ampliar(tela_visivel))
        cv2.imshow("mask", ampliar(mascara, ESCALA_MASK))

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord("q"):
            break
        elif tecla == ord("c"):
            tela[:] = 255
        elif tecla == ord("f"):
            # alterna tela cheia da janela Paint
            cheia = cv2.getWindowProperty(
                "Paint", cv2.WND_PROP_FULLSCREEN) == cv2.WINDOW_FULLSCREEN
            cv2.setWindowProperty("Paint", cv2.WND_PROP_FULLSCREEN,
                                  cv2.WINDOW_NORMAL if cheia
                                  else cv2.WINDOW_FULLSCREEN)
        elif tecla == ord("s"):
            cv2.imwrite("desenho.png", tela)
            print("Desenho salvo em desenho.png")

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()