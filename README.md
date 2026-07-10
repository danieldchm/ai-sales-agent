# AI SDR — Agente de Qualificação de Leads

MVP de um **agente de IA para pré-venda (SDR)** que qualifica leads de uma consultoria,
distinguindo demandas de **GenAI real** de casos melhor resolvidos por **RPA, BI ou automação
clássica** — reduzindo o tempo de consultores sêniores e melhorando o dimensionamento de propostas.

> Trabalho acadêmico — **MBA em AI Leadership / FIAP**.
> Status: **rascunho inicial** (definição de escopo).

## O que o agente faz (MVP)

A partir do texto de um lead (formulário + e-mail + briefing), o agente retorna:

1. **Classificação** da demanda: `GenAI real` | `RPA` | `BI` | `automação clássica`
2. **Nível de maturidade em IA** do prospect
3. **Perguntas de discovery** sugeridas
4. **Cases relevantes** da consultoria (via RAG)

O SDR sempre revisa a saída — **human-in-the-loop**.

## Documentação

- [`docs/genai-canvas.md`](docs/genai-canvas.md) — GenAI Canvas (transcrição do artefato original)
- [`docs/mvp-scope.md`](docs/mvp-scope.md) — Revisão crítica do canvas e definição do MVP

## Stack pretendida

| Camada     | Ferramenta                     |
|------------|--------------------------------|
| LLM        | Gemini via API                 |
| RAG        | Vector DB (Chroma) sobre cases |
| UI         | Streamlit                      |
| Linguagem  | Python                         |

**Fora do MVP (Fase 2):** transcrição de calls (Whisper), integração com CRM.

## Como rodar (a definir)

```bash
cp .env.example .env   # preencha GEMINI_API_KEY
# instruções de setup serão adicionadas conforme o MVP for implementado
```

## Estrutura

```
.
├── README.md
├── .env.example        # variáveis de ambiente (sem segredos)
├── .gitignore
└── docs/
    ├── genai-canvas.md # canvas original (rascunho)
    └── mvp-scope.md    # revisão + escopo do MVP
```
