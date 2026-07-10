# Base de cases — conhecimento para o RAG do AI SDR

20 cases estruturados para servir de base de conhecimento (RAG) do agente. Cada case ensina o
agente a reconhecer **sinais de diagnóstico** que separam uma demanda de **GenAI real** de uma
que é, na prática, **RPA**, **BI** (inclui modelagem preditiva/ML clássica) ou **automação
clássica** — o núcleo do problema definido no [GenAI Canvas](../../docs/genai-canvas.md).

## Metodologia e honestidade dos dados

Os cases são de dois tipos, identificados pelo campo `tipo_case`:

- **`real` (11 cases):** empresas e eventos reais, publicamente documentados na imprensa
  especializada (Bloomberg, CNBC, Forbes, STAT News, ABA Journal, etc.) e em relatórios
  acadêmicos/institucionais. Cada um traz suas fontes em `fontes`.
- **`composto` (9 cases):** cenários **ilustrativos**, sem vínculo com uma empresa real
  específica — construídos a partir de padrões de mercado (ex.: framework Gartner de
  RPA vs. IA) e de situações recorrentes de discovery comercial. Todos trazem
  `"empresa": null` e um campo `disclaimer` explícito.

Essa separação é intencional: casos reais dão credibilidade e riqueza de detalhe (números,
datas, consequências reais — inclusive falhas), enquanto os compostos preenchem lacunas de
setor/porte sem inventar afirmações sobre empresas reais que não podem ser verificadas.

## Distribuição

| Classificação | Qtde | Reais | Compostos |
|---|---|---|---|
| GenAI real | 7 | 5 | 2 |
| RPA | 5 | 2 | 3 |
| BI | 5 | 3 | 2 |
| Automação clássica | 3 | 1 | 2 |

De propósito, a base inclui tanto **sucessos** quanto **fracassos públicos** (Zillow, Watson for
Oncology, McDonald's/IBM, Amazon) — a lição de "por que deu errado" é tão útil para o
direcionamento de discovery quanto o "por que deu certo".

## Schema de cada case (`case-NN-slug.json`)

| Campo | Descrição |
|---|---|
| `id` | Identificador único (= nome do arquivo sem extensão) |
| `titulo` | Título curto do case |
| `tipo_case` | `real` ou `composto` |
| `empresa` | Nome da empresa (apenas se `tipo_case = real`; `null` caso contrário) |
| `industria`, `porte_prospect`, `regiao` | Metadados para filtragem/contexto |
| `sintoma_demanda_inicial` | O que o prospect pediu/achava que precisava |
| `classificacao_correta` | `GenAI real` \| `RPA` \| `BI` \| `Automação clássica` |
| `nuance` | Observação sobre zonas cinzentas (quando aplicável) |
| `sinais_diagnostico` | Lista de evidências que indicam a classificação correta |
| `abordagem_recomendada` | Resumo da solução/tecnologia recomendada |
| `perguntas_discovery_chave` | Perguntas que um vendedor pode usar para diagnosticar um caso análogo |
| `resultado_licao` | Desfecho real (ou lição pretendida, nos compostos) |
| `fontes` | Lista de `{titulo, url}` (vazia nos compostos sem citação direta) |
| `disclaimer` | Presente apenas nos `composto`, reforçando que é ilustrativo |

## Uso pretendido (ingestão no Qdrant)

Cada arquivo deve virar 1 ponto no Qdrant (collection `ai_sdr_cases`, 768 dimensões, distância
Cosine — já criada, ver [`README.md`](../../README.md) da raiz). O texto a ser embedado (via
`embeddinggemma` no Ollama) é a concatenação de `titulo + sintoma_demanda_inicial +
sinais_diagnostico + abordagem_recomendada`; os demais campos vão no `payload` do ponto para
serem devolvidos ao workflow do N8N como contexto/citação.
