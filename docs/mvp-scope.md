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
  - **Stack 100% local:** N8N (orquestração) + Ollama rodando modelo Gemma local (LLM) +
    Open WebUI (interface de chat, já disponível em container). Ver §3.
  - Isso **resolve diretamente** o risco de segurança de dados apontado no canvas original
    (nota 5): como o LLM roda localmente via Ollama, nenhum dado do prospect é enviado a uma
    API externa de terceiros.

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

**Entrada:** domínio do prospect (ex.: `itau.com.br`), informado pelo vendedor no chat (Open WebUI).

**Pipeline (com justificativa em cada etapa):**
1. **Research/enriquecimento** a partir do domínio — coleta informações públicas sobre a empresa
   (site institucional, notícias, vagas de emprego, sinais de maturidade digital/tech stack).
2. **RAG** sobre a base de cases da consultoria — recupera cases/soluções similares já entregues.
3. **Classificação** da demanda mais provável: `GenAI real` | `RPA` | `BI` | `automação clássica`.
4. **Nível de maturidade em IA** do prospect (ex.: inicial / em desenvolvimento / avançado).
5. **Direcionamento de estratégia para o vendedor**: manter a abordagem que o prospect já trouxe
   vs. propor um *shift* de estratégia; e se é necessário um **discovery mais profundo** antes de
   avançar.
6. **3–5 perguntas de discovery** sugeridas, adaptadas ao que já foi descoberto na pesquisa.

**Saída:** resumo estruturado (perfil da empresa + classificação + maturidade + recomendação de
direcionamento + perguntas + cases relevantes), entregue como mensagem no chat do Open WebUI.

**Fora do MVP (Fase 2+):** Whisper (transcrição de calls), integração com CRM, scoring histórico,
multiusuário/autenticação.

## 3. Arquitetura mínima proposta

```
[Vendedor informa o domínio no chat — Open WebUI]
                    │
                    ▼
        ┌───────────────────────┐
        │   N8N (orquestração)  │
        │  workflow disparado   │
        │  via webhook          │
        └──────────┬────────────┘
                    │
     ┌──────────────┼───────────────────┐
     ▼              ▼                   ▼
┌─────────┐  ┌───────────────┐   ┌──────────────┐
│ Research │  │  RAG retrieval │   │ Ollama (Gemma)│
│ (scraping│  │  base de cases │   │  LLM local    │
│ do site, │  │  (vector store)│   │  classificação│
│ notícias,│  └───────┬────────┘   │  + recomendação│
│  vagas)  │          │            └──────┬────────┘
└────┬─────┘          │                   │
     └──────────► compõe prompt ◄─────────┘
                       │
                       ▼
        Resposta estruturada → Open WebUI (chat)
```

- **UI:** Open WebUI (já disponível em container local) — interface de chat com o vendedor.
- **Orquestração:** N8N — recebe o domínio via webhook, executa scraping/research, consulta o
  RAG e chama o LLM, formata e devolve a resposta.
- **LLM:** Ollama rodando **`gemma4:12b-mlx`** (build otimizado para Apple Silicon) — sem
  chamadas a API externa; saída em JSON estruturado (schema fixo) sempre que possível.
- **RAG:** **Qdrant** como vector store sobre a base de cases da consultoria, consultado via
  node nativo do N8N.
- **Research/enriquecimento:** nodes de HTTP request + parsing de HTML no N8N para o site do
  domínio informado, combinados com consultas a uma instância local de **SearXNG** (busca de
  notícias, vagas, menções públicas) — sem custo por chamada e sem API key de terceiros.
- **Gatilho UI → N8N:** uma **Function/Pipe do Open WebUI** recebe a mensagem do vendedor
  (contendo o domínio), chama o webhook do N8N de forma síncrona e exibe a resposta no chat.

### Decisões de implementação (fechadas em 2026-07-10)

| Decisão | Escolha |
|---|---|
| Fonte de dados da pesquisa | Scraping do site + **SearXNG** self-hosted |
| Gatilho Open WebUI → N8N | **Pipe/Function** do Open WebUI chamando webhook do N8N |
| Vector store do RAG | **Qdrant** |
| Modelo LLM (Ollama) | **`gemma4:12b-mlx`** |

### Serviços adicionais que este pivot introduz

Além de Ollama, N8N e Open WebUI (já disponíveis), o MVP agora depende de subir localmente:
- **SearXNG** (busca self-hosted)
- **Qdrant** (vector store do RAG)

**Status (2026-07-10):** os três serviços foram subidos via `docker-compose.yml` e verificados
(N8N, SearXNG com formato JSON habilitado, Qdrant com a collection `ai_sdr_cases` criada).
A base de **20 cases** (ver [`data/cases/`](../data/cases/README.md)) foi pesquisada, curada,
embedada com `embeddinggemma` e indexada no Qdrant via
[`scripts/ingest_cases.py`](../scripts/ingest_cases.py) — recuperação semântica testada e
funcionando.

## 4. Métricas — tornar mensuráveis

| Indicador | Como medir no MVP | Baseline | Meta |
|---|---|---|---|
| Tempo de qualificação/lead | Cronometrar vendedor com vs. sem o agente | _(coletar)_ | −X% |
| Acurácia da classificação | Comparar contra rótulo de consultor sênior em um **conjunto-ouro** (~30 domínios/prospects) | — | ≥ Y% |
| Qualidade/relevância da pesquisa | O perfil da empresa gerado bate com o que um consultor levantaria manualmente? (1–5) | — | ≥ 4 |
| Qualidade do direcionamento sugerido | Avaliação 1–5 do vendedor: a recomendação (manter estratégia vs. shift) ajudou de fato? | — | ≥ 4 |
| Horas de pré-venda economizadas | Extrapolar do tempo/lead | — | — |

> O **conjunto-ouro de ~30 domínios de prospects rotulados** (classificação + maturidade
> esperadas, validadas por consultor sênior) é também o principal artefato de avaliação
> acadêmica do trabalho.

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
- [ ] **Pendente manual:** completar setup inicial do N8N, ativar o workflow e testar ponta a ponta (não pude fazer isso sem acesso à sua conta)
- [ ] Instalar a Function do Open WebUI (`openwebui/pipe_ai_sdr.py`) e testar no chat
- [ ] Criar conjunto-ouro de domínios/prospects rotulados para avaliação
