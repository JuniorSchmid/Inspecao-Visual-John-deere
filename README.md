# Green Check

Inspeção visual de adesivo de segurança com Python e OpenCV, desenvolvida em equipe para o Grand Prix SENAI de Inovação, num desafio da John Deere (2025).

Conferir se um adesivo obrigatório está na peça é uma verificação binária repetida centenas de vezes por turno, e é justamente por ser repetitiva que a falha passa. O Green Check transforma essa conferência numa pergunta fechada: o adesivo está nesta região da peça, na posição e no ângulo esperados?

## Como funciona

1. Com uma peça correta na frente da câmera, o operador captura o padrão: posição e rotação de referência do adesivo.
2. Em cada inspeção, a imagem é segmentada por cor no espaço HSV para separar a chapa verde do adesivo amarelo.
3. Dos contornos encontrados saem o centro e o ângulo do adesivo, comparados com o padrão dentro de uma tolerância configurável.
4. O resultado aparece na interface como aprovado ou reprovado, e cada inspeção fica registrada com a imagem e o horário.

A escolha foi começar por processamento de imagem clássico em vez de deep learning: cor, forma e posição do adesivo são estáveis, então o sistema fica leve, rápido e dá para explicar por que ele reprovou uma peça.

## Estrutura

```
PROJECT GREEN_CHECK/
├── sis.py                       # aplicação: câmera, detecção e interface (Tkinter)
├── config/sistema_config.json   # posição e rotação padrão, tolerâncias e limiares
└── logs/                        # imagens e registro das inspeções
```

## Executar

```bash
pip install opencv-python numpy pillow
python "PROJECT GREEN_CHECK/sis.py"
```

As tolerâncias ficam em `config/sistema_config.json` (padrão: ±50 px de posição e ±3° de rotação).

---

Case completo no [portfólio](https://www.juniorportfolio.blog/projetos/green-check).
