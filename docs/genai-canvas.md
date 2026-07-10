# GenAI Canvas — AI SDR (rascunho inicial)

> **Status:** Rascunho v0 — transcrição fiel do canvas original (FIAP / MBA em AI Leadership).
> Serve como ponto de partida para a definição do MVP. As críticas e ajustes estão em
> [`mvp-scope.md`](./mvp-scope.md).

---

## Problema
Qualificação manual de leads consome tempo de consultores sêniores. Muitas oportunidades
rotuladas como "IA" seriam resolvidas por RPA ou BI, gerando propostas mal dimensionadas e
queda na conversão.

## Como resolver sem IA?
- Checklist manual de qualificação
- Calls de discovery com cada prospect
- Scoring em planilha com rubrica manual

## Como resolver com GenAI?
- LLM classifica a lead: **GenAI real × RPA × BI × automação clássica**
- Atribui **nível de maturidade em IA** do prospect
- Sugere **abordagem e perguntas de discovery**
- **RAG** sobre base de cases da consultoria

## Para quem?
- SDR / pré-venda (usuário direto)
- Account executives
- Liderança comercial

## Dados necessários
- Formulários, e-mails, briefings e transcrições de calls
- Histórico de oportunidades do CRM
- Catálogo de serviços e análise de maturidade em IA e Tecnologia

## Ferramentas
- LLM via API (Gemini)
- RAG com Vector DB (base de cases)
- Integração com CRM *(integração futura)*
- Transcrição de calls (Whisper)

## Indicadores de sucesso
- Redução do tempo de qualificação por lead
- Acurácia da classificação vs. consultor sênior
- Aumento na taxa de conversão
- Horas de pré-venda economizadas

## Avaliação de impacto
> Escala: Baixo = 0, Médio = 5, Alto = 10

| Dimensão                  | Nota |
|---------------------------|:----:|
| ROI                       |  10  |
| Relevância tática         |  10  |
| Relevância estratégica    |  10  |
| Disponibilidade dos dados |  5   |
| Qualidade dos dados       |  5   |
| Requisitos de arquitetura |  5   |
| Segurança dos dados       |  5   |
