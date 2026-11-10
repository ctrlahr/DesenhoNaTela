# Desenho na Tela (Air Canvas)

Desenhe no ar usando a webcam: segure um objeto de uma cor (tampa de caneta,
bola, etc.), mova na frente da câmera e o programa desenha o trajeto na tela.

## Como funciona

1. A webcam captura a imagem e converte para HSV.
2. Uma máscara isola a cor do objeto que você segura.
3. O maior contorno da máscara vira a "ponta do pincel".
4. Ao mover o objeto, o programa liga os pontos numa tela branca (Paint).
5. Passando a ponta sobre os botões do topo você troca de cor ou limpa a tela.

## Requisitos

- Windows 10 ou 11 com webcam
- Python 3.9+ (testado com Python 3.13)
- Para usar só o executável, o Python **não** é necessário

## Rodar com Python

```bat
pip install -r requirements.txt
python main.py
```

## Gerar o executável (PyInstaller)

Dê um duplo clique em **`build_exe.bat`** (ou rode no terminal):

```bat
build_exe.bat
```

O script instala as dependências, gera o ícone e cria um **arquivo único** em:

```
dist\DesenhoNaTela.exe
```

Esse `.exe` não precisa de Python instalado e pode ser copiado para a Área de
Trabalho. Na primeira abertura ele demora alguns segundos (é o formato
"onefile" se descompactando).

Para gerar manualmente, sem o `.bat`:

```bat
python -m pip install -r requirements.txt
python -m PyInstaller --noconfirm --clean DesenhoNaTela.spec
```

### Teste rápido (sem webcam)

```bat
python main.py --autoteste
```

No executável:

```bat
dist\DesenhoNaTela.exe --autoteste
```

O código de saída `0` significa que a máscara, o desenho e os botões
funcionaram.

## Teclas

| Tecla | Ação |
| --- | --- |
| `q` ou `Esc` | Sair |
| `c` | Limpar tudo |
| `s` | Salvar desenho em PNG |
| `f` | Tela cheia na janela Paint |
| `m` | Mostrar/ocultar a janela da máscara |

Fechar a janela "Tracking" (ou "Color detectors") com o `X` também encerra o
programa.

O desenho é salvo em:

```
C:\Users\<seu usuário>\Pictures\DesenhoNaTela\desenho.png
```

## Ajustar a cor

A janela **Color detectors** tem sliders HSV. Os valores iniciais rastreiam
tons de azul. Aponte o objeto para a câmera e ajuste até a janela **mask**
ficar branca somente sobre ele:

- aumente **Lower Saturation** para ignorar objetos claros/acinzentados;
- aumente **Lower Value** para ignorar sombras escuras;
- se o objeto for vermelho, o matiz pode "dar a volta": use uma faixa que
  inclua os extremos (por exemplo, limite inferior 0 e superior 10, ou 170 a
  180).

Para mudar os valores iniciais, edite `LIMITE_INFERIOR_PADRAO` e
`LIMITE_SUPERIOR_PADRAO` no `main.py`.

## Problemas comuns

- **"Não foi possível abrir a webcam"**: feche outros programas que usam a
  câmera (Teams, OBS, navegador) e confira em *Configurações > Privacidade e
  segurança > Câmera* se o acesso está liberado para aplicativos da Área de
  Trabalho.
- **Janelas grandes demais / desalinhadas**: ajuste `ESCALA_EXIBICAO` no
  `main.py` (`1.0` = 640x480) e gere o executável de novo.
- **Travando ou lento**: use boa iluminação, reduza `ESCALA_EXIBICAO` e evite
  fundos com a mesma cor do objeto.
- **O executável não abre**: ele mostra uma caixa de erro do Windows; se nada
  aparecer, rode `dist\DesenhoNaTela.exe --autoteste` e verifique o código de
  saída.
- **Aviso do SmartScreen ("O Windows protegeu o seu PC")**: é normal em
  executáveis sem assinatura digital. Clique em *Mais informações* >
  *Executar assim mesmo*.

## Estrutura do projeto

```
main.py                      aplicação
requirements.txt             dependências
DesenhoNaTela.spec           configuração do PyInstaller
build_exe.bat                build do executável em um clique
assets/icone.ico             ícone do executável
assets/versao.txt            metadados de versão do executável
ferramentas/gerar_icone.py   gerador do ícone
dist/DesenhoNaTela.exe       executável gerado (não versionado)
```
