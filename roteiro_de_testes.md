# Roteiro de Testes: Sistema BlindDistance

Bem-vindo(a) ao roteiro de testes do **BlindDistance**, um assistente tecnológico para deficientes visuais baseado em visão estéreo. Este guia foi feito para que qualquer pessoa, mesmo sem conhecimento técnico avançado, consiga testar as funcionalidades do sistema na prática.

---

## 1. Preparação do Ambiente e Equipamento

Antes de começar os testes, verifique se tudo está pronto:
- **Câmeras:** O sistema utiliza duas webcams USB comuns fixas lado a lado (cerca de 6 a 7 cm de distância entre elas). Certifique-se de que ambas estão conectadas no computador.
- **Áudio:** O sistema "fala" e emite bipes. Verifique se o volume do seu computador, alto-falante ou fone de ouvido está ligado em uma altura agradável.
- **Espaço:** Escolha um local com algum espaço livre (pelo menos uns 3 metros à frente) e que contenha alguns objetos comuns (cadeira, mochila, garrafa, etc.) e paredes para os testes de colisão.
- **Calibração:** Assuma que a etapa de calibração das câmeras já foi feita por um técnico responsável e o sistema já está configurado.

---

## 2. Ligando o Sistema

Para iniciar o sistema, siga estes passos (ou peça para o técnico iniciar para você):

1. Abra o terminal (ou prompt de comando) no computador.
2. Certifique-se de que o ambiente virtual do Python está ativado (caso aplicável).
3. Execute o comando:
   ```bash
   python main.py
   ```
4. O sistema começará a carregar. Em poucos segundos, ele começará a analisar as imagens das câmeras em tempo real. Você deverá ouvir as respostas sonoras conforme se aproxima de objetos.

---

## 3. Realizando os Testes Práticos

Vamos testar cada uma das funções de segurança que o sistema oferece. Realize os testes abaixo de forma calma e segura.

### Teste A: Alerta de Colisão e Proximidade (Bipes)
**Objetivo:** Verificar se o sistema avisa quando você está prestes a bater em uma barreira (parede, porta fechada).

1. Com o sistema rodando, aponte as câmeras (ou caminhe lentamente com elas) em direção a uma parede lisa e plana.
2. Comece a cerca de 2 metros de distância e vá se aproximando aos poucos.
3. **O que deve acontecer:** Quando você chegar a menos de 1 metro da parede, o sistema deverá começar a emitir **bipes sonoros** (semelhante ao sensor de ré de um carro) alertando sobre a barreira iminente. Ao se afastar, os bipes devem parar.

### Teste B: Reconhecimento e Distância de Objetos (Voz)
**Objetivo:** Testar a inteligência artificial para ver se ela reconhece objetos e fala a que distância eles estão.

1. Posicione um objeto comum na frente das câmeras, entre 1 e 2 metros de distância (pode ser uma cadeira, uma pessoa, um celular ou um copo).
2. Aponte as câmeras diretamente para o objeto.
3. **O que deve acontecer:** A inteligência artificial identificará o objeto e cruzará com o cálculo de profundidade. O sistema deverá "falar" (usando voz sintetizada) o nome do objeto e a distância aproximada, por exemplo: *"Pessoa a 1 metro e meio"* ou *"Cadeira a 2 metros"*.

### Teste C: Prevenção de Quedas (Degraus e Buracos)
**Objetivo:** Verificar se o sistema detecta quando o chão acaba repentinamente, como em um degrau para baixo.

1. Vá até o topo de um lance de escadas (que desça) ou procure um local com um degrau alto e seguro (fique em uma distância segura para não cair!).
2. Aponte as câmeras levemente para baixo, como se você estivesse olhando para onde vai pisar, em direção à descida da escada.
3. **O que deve acontecer:** O sistema analisa constantemente a parte de baixo da imagem. Quando notar que o chão "sumiu" ou ficou repentinamente muito mais fundo, ele acionará um alerta verbal de emergência avisando sobre o risco de queda no piso.

---

## 4. Encerramento e Observações

Para encerrar o sistema a qualquer momento:
- Clique na janela principal do vídeo (se estiver visível na tela) e pressione a tecla `q` no teclado.
- O sistema será finalizado com segurança.

### O que anotar durante os testes:
- Os bipes tocaram na hora certa ou muito tarde?
- O volume e a clareza da voz estavam bons?
- O sistema demorou muito para falar o nome dos objetos (lag)?
- A detecção de escadas disparou algum alarme falso enquanto você andava no plano?

Com essas respostas, a equipe técnica poderá fazer ajustes (como afinar a calibração) para deixar o **BlindDistance** ainda mais seguro!

---
*Nota: Este documento foi revisado e corrigido por Inteligência Artificial, visando apenas a melhor ortografia e objetividade do texto.*
