# AI SDR — Agente de Qualificação de Leads

MVP de um **agente de IA para pré-venda (SDR)** que qualifica leads de uma consultoria,
distinguindo demandas de **GenAI real** de casos melhor resolvidos por **RPA, BI ou automação
clássica** — reduzindo o tempo de consultores sêniores e melhorando o dimensionamento de propostas.

> Trabalho acadêmico — **MBA em AI Leadership / FIAP**.
> Status: **rascunho inicial** (definição de escopo).

## O que o agente faz (MVP)

O vendedor informa apenas o **domínio do prospect** (ex.: `itau.com.br`) no chat. O agente então:

1. Faz **research/enriquecimento** automático sobre a empresa a partir do domínio (site
   institucional, notícias, vagas de emprego, sinais de maturidade digital)
2. Recupera **cases relevantes** da consultoria via RAG
3. **Classifica** a demanda mais provável: `GenAI real` | `RPA` | `BI` | `automação clássica`
4. Estima o **nível de maturidade em IA** do prospect
5. Recomenda o **direcionamento de estratégia**: manter a abordagem que o prospect já propôs vs.
   sugerir um *shift*, e se é necessário um discovery mais profundo
6. Sugere **perguntas de discovery** adaptadas ao que já foi levantado na pesquisa

O vendedor sempre revisa a recomendação — **human-in-the-loop**.

## Documentação

- [`docs/genai-canvas.md`](docs/genai-canvas.md) — GenAI Canvas (transcrição do artefato original)
- [`docs/mvp-scope.md`](docs/mvp-scope.md) — Revisão crítica do canvas, pivot de stack e escopo do MVP

## Stack

| Camada        | Ferramenta                                     |
|---------------|-------------------------------------------------|
| Orquestração  | N8N (workflow: research → RAG → LLM → resposta) |
| LLM           | Ollama, modelo Gemma **local**                   |
| Interface     | Open WebUI (já disponível em container)          |
| RAG           | Vector store sobre base de cases (via N8N)       |

Stack 100% local — nenhum dado do prospect é enviado a APIs externas de terceiros.

**Fora do MVP (Fase 2):** transcrição de calls (Whisper), integração com CRM.

## Como rodar (a definir)

Pressupõe Ollama, N8N e Open WebUI já disponíveis localmente. Instruções detalhadas (workflow do
N8N, configuração do webhook/pipe e do modelo Gemma no Ollama) serão adicionadas conforme o MVP
for implementado — ver decisões em aberto em [`docs/mvp-scope.md`](docs/mvp-scope.md#decisões-de-implementação-em-aberto).

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
