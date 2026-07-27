# BlindDistance — Guia Completo de Instalação e Uso

> Sistema de assistência para deficientes visuais baseado em visão estéreo computacional.

---

## Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Montagem do Hardware](#2-montagem-do-hardware)
3. [Instalação do Software](#3-instalação-do-software)
4. [Calibração das Câmeras](#4-calibração-das-câmeras)
5. [Executando o Sistema Principal](#5-executando-o-sistema-principal)
6. [Ferramentas Auxiliares](#6-ferramentas-auxiliares)
7. [Estrutura do Projeto](#7-estrutura-do-projeto)
8. [Solução de Problemas](#8-solução-de-problemas)

---

## 1. Pré-requisitos

### Hardware Necessário

| Item | Especificação | Observação |
|---|---|---|
| **2 webcams USB** | Qualquer webcam padrão com suporte a 640×480 | Devem ser do mesmo modelo para melhores resultados |
| **Suporte rígido** | Barra ou bracket que mantenha as câmeras fixas | Baseline (distância entre câmeras) de **6 a 7 cm** |
| **Tabuleiro de xadrez** | 8×6 cantos internos, quadrados de **30mm** | Imprima em papel A3 e cole em uma superfície plana e rígida |
| **Computador** | Processador multi-core (Intel i5/Ryzen 5 ou superior) | GPU dedicada é opcional mas melhora o desempenho |
| **Fones / Alto-falantes** | Qualquer dispositivo de saída de áudio | Necessário para os alertas sonoros e de voz |

### Software Necessário

| Requisito | Versão Mínima |
|---|---|
| **Python** | 3.12 ou superior (64-bit) |
| **pip** | Última versão disponível |
| **Git** | Qualquer versão recente |
| **Sistema Operacional** | Linux (Ubuntu 22.04+) ou Windows 10+ |

### Verificando o Python

Abra o terminal e execute:

```bash
python3 --version
```

Você deve ver algo como `Python 3.12.x` ou superior. Se não tiver o Python instalado:

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

**Windows:**
Baixe o instalador em [python.org](https://www.python.org/downloads/) e marque a opção **"Add Python to PATH"** durante a instalação.

---

## 2. Montagem do Hardware

### 2.1. Preparar o Suporte das Câmeras

O fator mais importante para a qualidade do mapa de profundidade é que **as duas câmeras estejam perfeitamente fixas e paralelas**.

```
  ┌─────────┐              ┌─────────┐
  │ Câmera  │◄── 6~7cm ──►│ Câmera  │
  │ ESQUERDA│              │ DIREITA │
  └────┬────┘              └────┬────┘
       │                        │
       └──── Suporte Rígido ────┘
```

**Dicas:**
- Use uma régua de alumínio, madeira plana, ou um bracket impresso em 3D
- As lentes devem estar na **mesma altura** e apontando na **mesma direção**
- A distância ideal entre os centros das lentes é de **6 a 7 centímetros**
- Fixe as câmeras com parafusos, cola quente ou braçadeiras — elas **não devem se mover**

### 2.2. Conectar as Câmeras

1. Conecte ambas as webcams em portas USB do computador
2. **Evite hubs USB** — conecte diretamente na placa-mãe se possível
3. Verifique se o sistema reconheceu ambas:

**Linux:**
```bash
ls /dev/video*
```
Você deve ver pelo menos dois dispositivos (ex: `/dev/video0` e `/dev/video2`).

**Windows:**
Abra o **Gerenciador de Dispositivos** e procure em "Câmeras".

### 2.3. Imprimir o Tabuleiro de Calibração

1. Baixe ou crie um padrão de tabuleiro de xadrez com:
   - **8 colunas × 6 linhas** de cantos internos (ou seja, 9×7 quadrados)
   - Cada quadrado com **30mm** de lado
2. Imprima em **papel A3** na escala 100% (sem redimensionar)
3. Cole o papel em uma superfície **plana e rígida** (papelão grosso, MDF, etc.)
4. **Verifique com uma régua** se os quadrados medem realmente 30mm

> ⚠️ Se os quadrados não medirem exatamente 30mm, ajuste o parâmetro `--square` na calibração.

---

## 3. Instalação do Software

### 3.1. Clonar o Repositório

```bash
git clone https://github.com/MarioCerconvis/BlindDistance.git
cd BlindDistance
git checkout Projeto-Visao-Computacional
```

### 3.2. Criar o Ambiente Virtual

**Linux/Mac:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Após ativar, você verá `(.venv)` no início da linha do terminal.

### 3.3. Instalar as Dependências

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

A instalação pode demorar alguns minutos pois inclui PyTorch e Ultralytics (YOLOv8).

### 3.4. (Opcional) Instalar opencv-contrib para Mapas de Profundidade Mais Suaves

```bash
pip install opencv-contrib-python
```

Isso habilita o **filtro WLS** (Weighted Least Squares) que melhora significativamente a qualidade do mapa de profundidade. O sistema funciona sem ele, mas é recomendado.

### 3.5. Verificar a Instalação

```bash
python3 -c "import cv2; print('OpenCV:', cv2.__version__)"
python3 -c "import torch; print('PyTorch:', torch.__version__)"
python3 -c "from ultralytics import YOLO; print('Ultralytics: OK')"
python3 -c "import pyttsx3; print('pyttsx3: OK')"
python3 -c "import pygame; print('pygame: OK')"
```

Todos devem retornar sem erro.

---

## 4. Calibração das Câmeras

> 🔴 **OBRIGATÓRIO** — A calibração deve ser feita **antes** de usar o sistema principal.  
> Sem calibração, o mapa de profundidade não será preciso.

### 4.1. Identificar os IDs das Câmeras

Primeiro, descubra qual câmera é a esquerda e qual é a direita:

```bash
python3 -c "
import cv2
for i in range(5):
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        print(f'Câmera encontrada no ID: {i}')
        cap.release()
"
```

Anote os IDs (geralmente `0` e `1`, ou `0` e `2`).

### 4.2. Executar a Calibração

```bash
python3 stereo_calibration.py --left 0 --right 1
```

> Se os IDs forem diferentes, ajuste os números. Se as câmeras estiverem trocadas (esquerda aparece na direita), adicione `--swap`.

### 4.3. Capturar Pares de Imagens

A janela de calibração mostrará o feed ao vivo das duas câmeras lado a lado.

1. **Posicione o tabuleiro** de modo que seja visível em **ambas** as câmeras
2. Pressione **ESPAÇO** para capturar um par
3. Se os cantos forem detectados em ambas, aparecerá a mensagem `CAPTURED pair #N`
4. Mova o tabuleiro para **posições e ângulos variados**:
   - Perto e longe
   - Inclinado para esquerda e direita
   - Inclinado para cima e para baixo
   - Em diferentes regiões do campo de visão
5. Capture **pelo menos 15 pares** (mais pares = melhor calibração, ideal 20-30)

```
   Boas posições para o tabuleiro:

   ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
   │  ╔═══╗            │  │            ╔═══╗  │  │                   │
   │  ║   ║            │  │            ║   ║  │  │     ╔═══╗        │
   │  ║   ║            │  │            ║   ║  │  │     ║   ║        │
   │  ╚═══╝            │  │            ╚═══╝  │  │     ╚═══╝        │
   │ Canto superior    │  │   Canto superior   │  │    Centro        │
   │ esquerdo          │  │   direito          │  │                  │
   └───────────────────┘  └───────────────────┘  └───────────────────┘

   ┌───────────────────┐  ┌───────────────────┐  ┌───────────────────┐
   │                   │  │                   │  │                   │
   │                   │  │       ╱═══╗       │  │                   │
   │  ╔═══╗            │  │      ╱   ╱        │  │            ╔═══╗  │
   │  ║   ║            │  │     ╱   ╱         │  │            ║   ║  │
   │  ╚═══╝            │  │    ╱═══╱          │  │            ╚═══╝  │
   │ Canto inferior    │  │   Inclinado       │  │  Canto inferior   │
   └───────────────────┘  └───────────────────┘  └───────────────────┘
```

### 4.4. Executar o Cálculo de Calibração

Quando tiver 15+ pares, pressione **c**. O processo leva ~30-60 segundos.

A saída exibirá:
```
[1/4] Calibrating left camera...
       Left RMS: 0.3254
[2/4] Calibrating right camera...
       Right RMS: 0.2987
[3/4] Running stereo calibration...
       Stereo RMS: 0.4521
[4/4] Computing rectification maps...

[OK] Calibration saved to: stereo_calibration_data.xml
     RMS Reprojection Error: 0.4521
```

> ✅ **RMS ideal:** menor que **0.5**. Se for maior que 1.0, recapture com mais cuidado.

### 4.5. Verificar a Retificação

Pressione **v** para ver a verificação. Uma imagem combinada aparecerá com **linhas verdes horizontais**:

- ✅ **BOM:** Os mesmos objetos aparecem na **mesma linha horizontal** em ambas as imagens
- ❌ **RUIM:** Objetos desalinhados verticalmente → recalibre com novos pares

Pressione **q** para sair da calibração.

O arquivo `stereo_calibration_data.xml` foi gerado na raiz do projeto. **Não delete este arquivo!**

---

## 5. Executando o Sistema Principal

### 5.1. Iniciar

```bash
python3 main.py
```

O sistema irá:
1. Carregar os dados de calibração
2. Abrir ambas as câmeras
3. Iniciar o modelo YOLOv8 (primeiro uso baixa o modelo automaticamente ~6MB)
4. Mostrar a janela "BlindDistance - AI Augmented View"

### 5.2. Controles

| Tecla | Ação |
|---|---|
| `q` | Sair do programa |
| `r` | Ativar/pausar gravação de dados |
| `1` | Label: `clear` (caminho livre) |
| `2` | Label: `person` (pessoa) |
| `3` | Label: `wall` (parede) |
| `4` | Label: `furniture` (mobília) |
| `5` | Label: `other_obstacle` (outro obstáculo) |

### 5.3. O que o Sistema Faz

Quando rodando, o sistema executa simultaneamente:

1. **Grade de Proximidade:** Pontos verdes/vermelhos na tela. Vermelho = objeto a menos de 1 metro → emite **bipe sonoro**
2. **Detecção de Objetos (YOLOv8):** Caixas ao redor de objetos reconhecidos com distância em metros
3. **Alerta de Voz:** Se um objeto reconhecido está a menos de 1 metro, o sistema fala: *"Warning! [objeto] at [X] meters."*
4. **Detecção de Queda:** Se o terço inferior da imagem mostra profundidade anormalmente grande (buraco/escada), o sistema fala: *"Warning! Drop ahead."*

---

## 6. Ferramentas Auxiliares

### 6.1. Ajuste de Parâmetros de Profundidade (`stereo_tuner.py`)

Se a qualidade do mapa de profundidade não estiver boa:

```bash
python3 stereo_tuner.py
```

Esta ferramenta mostra:
- **Linha superior:** Par de imagens retificadas com linhas epipolares
- **Linha inferior:** Mapa de disparidade + Mapa de profundidade em cores

Use os **trackbars** para ajustar:

| Parâmetro | Efeito |
|---|---|
| `numDisparities` | Maior = detecta objetos mais próximos, mas mais lento |
| `blockSize` | Maior = mais suave, mas perde detalhes finos |
| `uniquenessRatio` | Maior = menos ruído, mas perde cobertura |
| `speckleWindowSize` | Maior = remove mais ruído pontual |
| `speckleRange` | Controla tolerância do filtro de speckle |

Pressione **q** para sair.

### 6.2. Diagnóstico de Detecção de Queda (`debug_floor_drop.py`)

Para ajustar a detecção de buracos/escadas:

```bash
python3 debug_floor_drop.py
```

| Tecla | Ação |
|---|---|
| `c` | Calibrar a baseline do piso (aponte para chão plano primeiro) |
| `s` | Salvar snapshot para análise offline |
| `q` | Sair |

A tela mostra:
- **Verde** = piso normal
- **Vermelho** = possível buraco/queda
- **Azul** = sem retorno de profundidade

---

## 7. Estrutura do Projeto

```
BlindDistance/
├── stereo_calibration.py      # 🔧 Ferramenta de calibração (executar primeiro)
├── stereo_camera.py           # 📷 Classe StereoCamera (captura + profundidade)
├── stereo_tuner.py            # 🎛️  Ajuste de parâmetros em tempo real
├── main.py                    # 🚀 Sistema principal
├── debug_floor_drop.py        # 🔍 Diagnóstico de detecção de queda
├── data_recorder.py           # 💾 Gravação de dados para treinamento
├── utils/
│   ├── audio_feedback.py      # 🔊 Alertas sonoros e voz (pyttsx3 + pygame)
│   └── vision.py              # 🤖 Detecção de objetos (YOLOv8 Nano)
├── requirements.txt           # 📦 Dependências Python
├── .gitignore
├── README.md
├── INSTALACAO_E_USO.md        # 📖 Este guia
├── Assistente para Deficientes Visuais.md  # 📄 Modelagem funcional
│
├── stereo_calibration_data.xml  # (gerado pela calibração)
├── calibration_images/          # (fotos de calibração salvas)
└── dataset/                     # (dados gravados para treinamento)
```

---

## 8. Solução de Problemas

### "Calibration file not found"

O arquivo `stereo_calibration_data.xml` não existe. Execute a calibração primeiro:
```bash
python3 stereo_calibration.py
```

### "Cannot open camera X"

- Verifique se as câmeras estão conectadas: `ls /dev/video*`
- Feche outros programas que possam estar usando as câmeras (Zoom, Google Meet, etc.)
- Tente IDs diferentes: `--left 0 --right 2`

### Câmeras trocadas (esquerda/direita)

Use o argumento `--swap`:
```bash
python3 stereo_calibration.py --swap
```

### RMS de calibração muito alto (> 1.0)

- Certifique-se que o tabuleiro está **plano** (sem ondulações)
- Verifique se as medidas dos quadrados estão corretas (use `--square` para ajustar)
- Capture pares com o tabuleiro em **posições variadas** (centro, cantos, inclinado)
- Evite reflexos e sombras fortes no tabuleiro
- Capture pelo menos **20-25 pares**

### Mapa de profundidade com muito ruído

- Recalibre com mais pares de imagens
- Instale `opencv-contrib-python` para ativar o filtro WLS
- Use `stereo_tuner.py` para ajustar os parâmetros
- Garanta boa iluminação (evite luz direta na lente)

### FPS baixo (< 15)

- Reduza `numDisparities` (em `stereo_camera.py`) de 128 para 64
- Aumente `blockSize` de 9 para 11
- Feche outros programas pesados
- Se tiver GPU NVIDIA, instale PyTorch com CUDA para acelerar o YOLOv8

### Áudio não funciona

**Linux:**
```bash
sudo apt install espeak
```

**Windows:**
O pyttsx3 usa o SAPI5 nativo do Windows, deve funcionar automaticamente.

### YOLOv8 lento no primeiro uso

Na primeira execução, o modelo `yolov8n.pt` (~6MB) é baixado automaticamente. Isso é normal e acontece apenas uma vez.

---

> _Desenvolvido como parte do projeto de Visão Computacional — BlindDistance._
