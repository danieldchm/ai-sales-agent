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

## Arquitetura do Agente

O diagrama abaixo ilustra o fluxo técnico do agente, agrupando os processos em módulos lógicos.

```mermaid
flowchart TD

    %% Definindo os nós com formas modernas
    User([👤 Vendedor / SDR])
    User2([👤 Admin])
    ChatIn(((🏁 INÍCIO: N8N Chat Trigger)))
    ChatOut(((🎯 FIM: Resposta Final)))
    
    subgraph Frontend [Interação com Usuário]
        direction TB
        User -->|Informa Domínio| ChatIn
        ChatOut -.->|Recomendação Final| User
    end

    subgraph DataEnrichment [🔎 Módulo de Enriquecimento]
        direction TB
        ExtrairDominio(Extrair Domínio)
        ScrapingSite{{Scraping do Site Institucional}}
        DetectSetor(Heurística de Setor)
        SearxngEmpresa[🌐 SearXNG: Empresa]
        SearxngSetor[🌐 SearXNG: Setor IA]
        SearxngMercado[🌐 SearXNG: Mercado]
        
        ExtrairDominio --> ScrapingSite
        ScrapingSite --> DetectSetor
        DetectSetor --> SearxngEmpresa & SearxngSetor & SearxngMercado
    end

    subgraph Financial [📊 Pipeline Financeiro B3/CVM]
        direction TB
        BrasilAPI(Consultar CNPJ BrasilAPI)
        TickersB3(Buscar Tickers brapi)
        MatchB3{Listada na B3?}
        DownloadCVM[📥 Baixar ITR Zip CVM]
        ParseCVM[⚙️ Parse CSV DRE]
        ChunksCVM(Chunks Financeiros)
        
        FormTrigger[📤 Upload Manual de PDF] --> ParsePDF[Extrair Texto do PDF] --> ChunksManual(Chunks do Upload)

        BrasilAPI --> TickersB3 --> MatchB3
        MatchB3 -- Sim --> DownloadCVM --> ParseCVM --> ChunksCVM
        MatchB3 -- Não --> SkipCVM(Pular Dados Financeiros)
    end

    subgraph VectorDB [🧠 Vector Retrieval & RAG]
        direction TB
        CompilaPerfil(Compilar Perfil)
        EmbedOllama((Ollama Embedding))
        QdrantCases[(Qdrant: Base de Cases)]
        QdrantFinance[(Qdrant: Relatórios)]
        
        EmbedOllama --> QdrantCases & QdrantFinance
    end

    subgraph LLMReasoning [🤖 Motor Cognitivo]
        direction TB
        MontarPrompt(Montar Prompt Estruturado)
        LangChainMem[(Window Buffer Memory)]
        OllamaLLM{Ollama local: gemma4:12b-mlx}
        ParseJSON(Parse JSON & Formatação)
    end

    %% Conexões entre os Subgráficos
    ChatIn --> ExtrairDominio
    User2 -.->|Envia Relatório RI| FormTrigger

    ScrapingSite --> BrasilAPI
    
    SearxngEmpresa & SearxngSetor & SearxngMercado & SkipCVM --> CompilaPerfil
    
    ChunksCVM & ChunksManual --> EmbedData((Embed Dados)) --> QdrantFinance
    
    CompilaPerfil --> EmbedOllama
    
    QdrantCases & QdrantFinance -->|Contexto Relevante| MontarPrompt
    
    MontarPrompt --> LangChainMem --> OllamaLLM --> ParseJSON
    ParseJSON --> ChatOut

    %% Estilos de nós para dar um visual clean
    classDef default fill:#f8fafc,stroke:#cbd5e1,stroke-width:1px,color:#334155;
    classDef primary fill:#3b82f6,stroke:#2563eb,stroke-width:2px,color:#ffffff;
    classDef success fill:#10b981,stroke:#059669,stroke-width:2px,color:#ffffff;
    classDef warning fill:#f59e0b,stroke:#d97706,stroke-width:2px,color:#ffffff;
    classDef database fill:#6366f1,stroke:#4f46e5,stroke-width:2px,color:#ffffff;
    classDef trigger fill:#ec4899,stroke:#db2777,stroke-width:2px,color:#ffffff;
    classDef startEnd fill:#0f172a,stroke:#3b82f6,stroke-width:4px,color:#ffffff,font-weight:bold;

    class User,User2 trigger;
    class ChatIn,ChatOut startEnd;
    class OllamaLLM,EmbedOllama,EmbedData success;
    class QdrantCases,QdrantFinance database;
    class MatchB3 warning;
```

## Documentação

- [`docs/genai-canvas.md`](docs/genai-canvas.md) — GenAI Canvas (transcrição do artefato original)
- [`docs/mvp-scope.md`](docs/mvp-scope.md) — Revisão crítica do canvas, pivot de stack e escopo do MVP
- [`docs/llm-output-schema.md`](docs/llm-output-schema.md) — Schema JSON da saída do LLM (classificação estruturada)
- [`n8n/workflows/README.md`](n8n/workflows/README.md) — Workflow do N8N: como abrir, ativar e testar

## Stack

| Camada        | Ferramenta                                              |
|---------------|----------------------------------------------------------|
| Orquestração  | N8N (workflow: research → RAG → LLM → resposta)         |
| LLM           | Ollama, modelo local `gemma4:12b-mlx` |
| Interface     | Chat nativo do N8N (node "Chat - Recebe Prompt")        |
| Research      | SearXNG self-hosted + scraping do site do prospect + dados abertos da CVM (empresas B3) |
| RAG           | Qdrant (vector store da base de cases + relatórios financeiros), via node do N8N |

**Fora do MVP (Fase 2):** transcrição de calls (Whisper), integração com CRM.

## Como rodar

Pressupõe Ollama já disponível localmente (fora deste compose). Sobe **N8N**,
**SearXNG** e **Qdrant**:

```bash
docker compose up -d
```

| Serviço | URL (do host) | URL (de dentro do N8N) |
|---|---|---|
| N8N        | http://localhost:5678 | — |
| SearXNG    | http://localhost:8080 | `http://searxng:8080` |
| Qdrant     | http://localhost:6333 | `http://qdrant:6333`  |
| Ollama     | http://localhost:11434 | `http://host.docker.internal:11434` |

Criar a collection do Qdrant para a base de cases (768 dimensões, compatível com o modelo de
embedding `embeddinggemma` do Ollama) e indexar os 20 cases curados:

```bash
curl -X PUT "http://localhost:6333/collections/ai_sdr_cases" \
  -H "Content-Type: application/json" \
  -d '{"vectors": {"size": 768, "distance": "Cosine"}}'

pip install -r requirements.txt
python3 scripts/ingest_cases.py
```

Por fim, siga [`n8n/workflows/README.md`](n8n/workflows/README.md) para completar o setup inicial
do N8N (criar sua conta de owner), ativar o workflow **"AI SDR - Qualificação de Leads"** (já
importado) e testar pelo painel de chat nativo do próprio N8N.

## Base de conhecimento (RAG)

[`data/cases/`](data/cases/README.md) contém 20 cases pesquisados e curados (11 reais e
documentados publicamente + 9 cenários compostos claramente identificados) que ensinam o agente
a distinguir GenAI real de RPA/BI/automação clássica. Já indexados no Qdrant.

## Workflow N8N

- [`n8n/workflows/ai-sdr-qualification.json`](n8n/workflows/ai-sdr-qualification.json) — pipeline
  completo (chat → research → RAG → Ollama/Gemma com memória por sessão → resposta), já importado
  no seu N8N local
- [`n8n/schemas/llm-output.schema.json`](n8n/schemas/llm-output.schema.json) — schema JSON usado
  na chamada estruturada ao Gemma (ver [`docs/llm-output-schema.md`](docs/llm-output-schema.md))

## Estrutura

```
.
├── README.md
├── docker-compose.yml   # N8N + SearXNG + Qdrant
├── requirements.txt     # dependências Python (scripts utilitários)
├── .env.example         # variáveis de ambiente (sem segredos)
├── .gitignore
├── data/
│   └── cases/           # 20 cases curados (base de conhecimento do RAG)
├── scripts/
│   └── ingest_cases.py  # gera embeddings (Ollama) e indexa os cases no Qdrant
├── searxng/
│   └── settings.yml     # habilita formato JSON (consumido pelo N8N)
├── n8n/
│   ├── workflows/
│   │   ├── ai-sdr-qualification.json  # pipeline completo (58 nodes, incluindo CVM/B3, upload manual e notas adesivas)
│   │   └── README.md                  # como abrir, ativar e testar
│   └── schemas/
│       └── llm-output.schema.json     # schema JSON da saída do Gemma
└── docs/
    ├── genai-canvas.md         # canvas original (rascunho)
    ├── mvp-scope.md            # revisão + escopo do MVP
    └── llm-output-schema.md    # schema JSON documentado com exemplo
```
