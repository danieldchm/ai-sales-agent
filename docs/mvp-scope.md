# Definição do MVP — AI SDR (rascunho)

> Documento derivado da revisão do [GenAI Canvas](./genai-canvas.md).
> Objetivo: transformar o canvas em um escopo **enxuto e demonstrável** para a entrega do MBA.

## 0. Changelog de escopo

- **v0 (canvas original):** entrada = texto do lead colado pelo SDR; stack proposta =
  Streamlit + Gemini API + Chroma.
- **v1 (atual):** pivot de stack e de entrada — decisão do autor do projeto.
  - **Entrada agora é o domínio do prospect** (ex.: `itau.com.br`). O próprio agente faz a
    **pesquisa/enriquecimento** sobre a empresa a partir do domínio, em vez de depender de o SDR
    já ter formulário/e-mail/briefing em mãos. Isso amplia o escopo técnico (adiciona uma etapa
    de research automatizado) mas aumenta o valor: o agente funciona com o mínimo de informação
    que o vendedor normalmente já tem (o site do prospect).
  - **Stack 100% local:** N8N (orquestração + **chat nativo**, node "Chat - Recebe Prompt") +
    Ollama rodando modelo Gemma local (LLM) + Qdrant (vector store) + SearXNG (busca). Ver §3.
    *(A camada de Open WebUI proposta na v0 foi removida — o trigger de chat nativo do N8N já
    resolve o problema de sessão órfã e elimina uma dependência.)*
  - Isso **resolve diretamente** o risco de segurança de dados apontado no canvas original
    (nota 5): como o LLM roda localmente via Ollama, nenhum dado do prospect é enviado a uma
    API externa de terceiros.
  - **v2 (2026-07): enriquecimento ampliado** — além do scraping do site, o research passou a
    fazer 3 buscas paralelas no SearXNG (empresa, setor, mercado) e, para empresas listadas na
    **B3**, a cruzar com **dados oficiais da CVM** (DRE dos ITRs) e com **relatórios de RI
    enviados manualmente** (upload de PDF). Ver §2 e §3.

## 1. Revisão crítica do canvas

O canvas está forte na **motivação de negócio** (ROI, relevância tática e estratégica = 10) e o
usuário-alvo está bem definido (SDR/pré-venda). Os pontos de atenção — e que definem o recorte do
MVP — são as notas médias (5) em **disponibilidade/qualidade de dados**, **arquitetura** e
**segurança**.

| Ponto forte | Risco / lacuna | Decisão para o MVP |
|---|---|---|
| Problema claro e usuário direto (SDR) | — | Manter foco no SDR; um único fluxo ponta a ponta |
| Diferencial GenAI vs RPA/BI/automação | Classificação pode errar (alucinação) | **Human-in-the-loop**: SDR sempre revisa e edita a saída |
| RAG sobre base de cases | Base de cases pode não existir/estar curada | Começar com **5–15 cases curados** em `data/`; expandir depois |
| Transcrição de calls (Whisper) | Aumenta escopo e custo do MVP | **Fora do MVP** → Fase 2 |
| Integração com CRM | Já marcada como "futura" | **Fora do MVP** → Fase 2 (entrada por texto colado) |
| Métricas de sucesso | Sem baseline nem meta numérica | Definir baseline + meta (ver §4) |
| Segurança dos dados (nota 5) | Lead contém dados de prospect/PII enviados à API | **Resolvido pelo pivot de stack**: LLM local (Ollama) — nenhum dado sai do ambiente (ver §0 e §5) |

## 2. Escopo do MVP (o que entra)

**Entrada:** domínio do prospect (ex.: `itau.com.br`), com contexto/dor opcional na mesma mensagem,
informado pelo vendedor no **chat nativo do N8N**.

**Pipeline (com justificativa em cada etapa):**
1. **Research/enriquecimento** a partir do domínio — scraping do site institucional + **3 buscas
   paralelas no SearXNG** (empresa, setor/indústria, mercado/concorrentes).
2. **Dados financeiros oficiais (empresas B3):** quando o prospect é identificado como companhia
   negociada na bolsa brasileira, cruza com os **dados abertos da CVM** (DRE Consolidado dos ITRs)
   e com **relatórios de RI enviados manualmente** (PDF), indexando tudo no Qdrant.
3. **RAG** sobre a base de cases da consultoria — recupera cases/soluções similares já entregues
   (busca guiada pela dor descrita pelo vendedor, para não poluir com o ramo da empresa).
4. **Classificação** da demanda mais provável: `GenAI real` | `RPA` | `BI` | `automação clássica`.
5. **Nível de maturidade em IA** do prospect (ex.: inicial / em desenvolvimento / avançado).
6. **Direcionamento de estratégia para o vendedor**: manter a abordagem que o prospect já trouxe
   vs. propor um *shift* de estratégia; e se é necessário um **discovery mais profundo** antes de
   avançar.
7. **3–5 perguntas de discovery** sugeridas, adaptadas ao que já foi descoberto na pesquisa.

**Saída:** resumo estruturado (perfil da empresa + classificação + maturidade + recomendação de
direcionamento + perguntas + cases relevantes), entregue como mensagem no **chat nativo do N8N**.

**Fora do MVP (Fase 2+):** Whisper (transcrição de calls), integração com CRM, scoring histórico,
multiusuário/autenticação.

## 3. Arquitetura mínima proposta

```
[Vendedor informa o domínio no chat nativo do N8N]
                    │
                    ▼
        ┌───────────────────────┐
        │   N8N (orquestração)  │
        │  chat trigger nativo  │
        └──────────┬────────────┘
                    │
     ┌──────────────┼───────────────────────────────┐
     ▼              ▼                                ▼
┌──────────┐  ┌──────────────────┐          ┌───────────────┐
│ Research │  │ Financeiro B3     │          │  RAG retrieval │
│ scraping │  │ CVM (DRE/ITR) +   │          │  base de cases │
│ + 3×     │  │ upload manual PDF │          │  (Qdrant)      │
│ SearXNG  │  │ → Qdrant          │          └───────┬────────┘
└────┬─────┘  └────────┬──────────┘                  │
     └─────────────────┼───────────► compõe prompt ◄─┘
                       │                   │
                       ▼                   ▼
                              ┌──────────────────┐
                              │ Ollama (Gemma)    │
                              │ LLM local +       │
                              │ memória p/ sessão │
                              └────────┬──────────┘
                                       ▼
                    Resposta estruturada → chat nativo do N8N
```

- **UI:** **chat nativo do N8N** (node "Chat - Recebe Prompt") — sem camada de UI externa; cada
  janela de chat tem memória própria por sessão (Window Buffer Memory, últimas 6 interações).
- **Orquestração:** N8N — recebe o domínio (+ contexto opcional), executa research/scraping, o
  pipeline financeiro B3/CVM, consulta o RAG e chama o LLM, formata e devolve a resposta.
- **LLM:** Ollama rodando **`gemma4:12b-mlx`** (build otimizado para Apple Silicon) — sem
  chamadas a API externa. O schema JSON é aplicado via exemplo embutido no prompt + parsing
  tolerante (o parâmetro `format` do Ollama é ignorado por este modelo servido via MLX — ver
  [`llm-output-schema.md`](./llm-output-schema.md)).
- **RAG:** **Qdrant** como vector store, com duas collections — `ai_sdr_cases` (base de cases) e
  `ai_sdr_relatorios_financeiros` (chunks de CVM + PDFs manuais) — consultadas via node do N8N.
- **Research/enriquecimento:** nodes de HTTP request + parsing de HTML para o site do domínio,
  combinados com **3 buscas paralelas** a uma instância local de **SearXNG** (empresa, setor,
  mercado) — sem custo por chamada e sem API key de terceiros.
- **Dados financeiros (B3):** detecção via BrasilAPI (CNPJ→razão social) + brapi.dev (tickers),
  cruzamento com dados abertos da **CVM** (cadastro + ITRs), mais um formulário de **upload manual
  de PDF** de RI — ambos indexados na mesma collection financeira do Qdrant.

### Decisões de implementação

| Decisão | Escolha |
|---|---|
| Fonte de dados da pesquisa | Scraping do site + **3× SearXNG** self-hosted |
| Interface de chat | **Chat trigger nativo do N8N** (Open WebUI removido) |
| Dados financeiros de empresas B3 | **Dados abertos da CVM** (ITR/DRE) + upload manual de PDF |
| Vector store do RAG | **Qdrant** (2 collections) |
| Modelo LLM (Ollama) | **`gemma4:12b-mlx`** |

### Serviços que este pivot introduz

Além de Ollama e N8N (já disponíveis), o MVP depende de subir localmente:
- **SearXNG** (busca self-hosted)
- **Qdrant** (vector store do RAG)

**Status (2026-07-13):** os serviços foram subidos via `docker-compose.yml` e verificados
(N8N com chat nativo, SearXNG com formato JSON habilitado, Qdrant com as collections
`ai_sdr_cases` e `ai_sdr_relatorios_financeiros` criadas).
A base de **20 cases** (ver [`data/cases/`](../data/cases/README.md)) foi pesquisada, curada,
embedada com `embeddinggemma` e indexada no Qdrant via
[`scripts/ingest_cases.py`](../scripts/ingest_cases.py) — recuperação semântica testada e
funcionando.

## 4. Métricas — tornar mensuráveis

### 4.1 Desempenho técnico (já medido)

Benchmarks de execuções reais no hardware do autor (Apple Silicon, Ollama local) — ver detalhes em
[`n8n/workflows/README.md`](../n8n/workflows/README.md#performance-observada-hardware-do-usuário):

| Indicador | Valor observado |
|---|---|
| Tempo de resposta ponta a ponta (`weg.net`, execução #93, com CVM + PDF manual) | **~2min56s** |
| Gargalo — classificação com Gemma (`gemma4:12b-mlx`) | ~100–200s, sensível ao tamanho do prompt |
| Research (scraping + 3× SearXNG) e embeddings | poucos segundos cada |
| Download/descompactação dos ITRs da CVM (empresa listada) | ~10–30s |

### 4.2 Métricas de negócio (a coletar com o conjunto-ouro)

| Indicador | Como medir no MVP | Baseline | Meta |
|---|---|---|---|
| Tempo de qualificação/lead | Cronometrar vendedor com vs. sem o agente | _(coletar)_ | −X% |
| Acurácia da classificação | Comparar contra rótulo de consultor sênior em um **conjunto-ouro** (~30 domínios/prospects) | _(não medido)_ | ≥ Y% |
| Qualidade/relevância da pesquisa | O perfil da empresa gerado bate com o que um consultor levantaria manualmente? (1–5) | _(não medido)_ | ≥ 4 |
| Qualidade do direcionamento sugerido | Avaliação 1–5 do vendedor: a recomendação (manter estratégia vs. shift) ajudou de fato? | _(não medido)_ | ≥ 4 |
| Horas de pré-venda economizadas | Extrapolar do tempo/lead | _(não medido)_ | — |

> **Ainda não medido:** as métricas de negócio dependem do **conjunto-ouro de ~30 domínios de
> prospects rotulados** (classificação + maturidade esperadas, validadas por consultor sênior),
> que é também o principal artefato de avaliação acadêmica do trabalho e ainda está por construir
> (ver §6).

## 5. Governança & segurança (ângulo AI Leadership)

- **LLM 100% local (Ollama/Gemma):** nenhum dado do prospect ou do research é enviado a uma API
  de terceiros — mitiga o risco de segurança de dados apontado no canvas original.
- A etapa de **research/scraping** deve respeitar `robots.txt`, limites de taxa e coletar apenas
  informação pública — não é reconhecimento invasivo nem coleta de dados pessoais sensíveis.
- Registrar **disclaimer**: a saída é uma recomendação de direcionamento, a decisão final sobre
  estratégia e discovery é do vendedor (**human-in-the-loop**).
- Documentar riscos: viés e alucinação do modelo local (Gemma tende a ter menos capacidade que
  modelos de fronteira — validar acurácia no conjunto-ouro antes de confiar cegamente), dados
  desatualizados ou incompletos vindos do research automatizado.

## 6. Próximos passos

- [x] Fechar as 3 decisões de implementação em aberto (§3)
- [ ] Validar este recorte com o professor/orientador
- [x] Subir N8N + SearXNG + Qdrant via docker-compose
- [x] Montar base de cases curada (`data/cases/`, 20 itens) e indexar no Qdrant
- [x] Definir schema JSON da saída do LLM (ver [`docs/llm-output-schema.md`](./llm-output-schema.md))
- [x] Implementar workflow N8N: research → RAG → Ollama (Gemma) → resposta (ver [`n8n/workflows/`](../n8n/workflows/README.md))
- [x] Setup inicial do N8N, ativação do workflow e **teste ponta a ponta com sucesso** (domínio real `weg.net`, ~2min56s de resposta)
- [x] Migrar a interface para o **chat nativo do N8N** (camada Open WebUI removida do processo)
- [x] Adicionar "deep research" (3 buscas paralelas no SearXNG: empresa, setor, mercado)
- [x] Adicionar pipeline financeiro B3 via **dados abertos da CVM** (ITR/DRE) + **upload manual de PDF**
- [ ] Criar conjunto-ouro de domínios/prospects rotulados para avaliação
