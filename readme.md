# Air Canvas - desenhe no ar usando a webcam.

## Como funciona:
1. A webcam captura a imagem e converte para HSV.
2. Uma máscara isola a cor do objeto que você segura (ponta de caneta, tampa, etc.).
3. O maior contorno da máscara vira a "ponta do pincel".
4. Ao mover o objeto, o programa liga os pontos numa tela branca (Paint).
5. Passando a ponta sobre os botões do topo você troca de cor ou limpa a tela.

## Teclas:
  q = sair | c = limpar tudo | s = salvar desenho em PNG | f = tela cheia do Paint

## Instalação:
  pip install opencv-python numpy