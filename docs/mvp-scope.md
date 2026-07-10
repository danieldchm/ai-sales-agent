# Definição do MVP — AI SDR (rascunho)

> Documento derivado da revisão do [GenAI Canvas](./genai-canvas.md).
> Objetivo: transformar o canvas em um escopo **enxuto e demonstrável** para a entrega do MBA.

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
| Segurança dos dados (nota 5) | Lead contém dados de prospect/PII enviados à API | Anonimização + flag de não-treinamento + política de dados (ver §5) |

## 2. Escopo do MVP (o que entra)

**Entrada:** texto do lead colado pelo SDR (formulário + e-mail + briefing).

**Saída estruturada (com justificativa):**
1. **Classificação** da demanda: `GenAI real` | `RPA` | `BI` | `automação clássica`
2. **Nível de maturidade em IA** do prospect (ex.: inicial / em desenvolvimento / avançado)
3. **3–5 perguntas de discovery** sugeridas
4. **Cases relevantes** recuperados via RAG (com fonte)

**Fora do MVP (Fase 2+):** Whisper, integração CRM, scoring histórico, multiusuário/autenticação.

## 3. Arquitetura mínima proposta

```
[SDR cola o lead]
        │
        ▼
  ┌─────────────┐     ┌──────────────────────┐
  │  App (UI)   │────▶│  Orquestração (Python)│
  │  Streamlit  │     │  - prompt de classif. │
  └─────────────┘     │  - RAG retrieval      │
        ▲             └───────┬──────────┬─────┘
        │                     │          │
        │             ┌───────▼───┐  ┌───▼─────────┐
        │             │ Gemini API│  │ Vector DB   │
        └─────────────│  (LLM)    │  │ (Chroma)    │
          saída        └───────────┘  │ base cases  │
          estruturada                 └─────────────┘
```

- **LLM:** Gemini via API, saída em JSON estruturado (schema fixo)
- **RAG:** Chroma/FAISS local sobre base de cases curada
- **UI:** Streamlit (rápido de demonstrar em banca)

## 4. Métricas — tornar mensuráveis

| Indicador | Como medir no MVP | Baseline | Meta |
|---|---|---|---|
| Tempo de qualificação/lead | Cronometrar SDR com vs. sem o agente | _(coletar)_ | −X% |
| Acurácia da classificação | Comparar contra rótulo de consultor sênior em um **conjunto-ouro** (~30 leads) | — | ≥ Y% |
| Qualidade da abordagem sugerida | Avaliação 1–5 por consultor sênior | — | ≥ 4 |
| Horas de pré-venda economizadas | Extrapolar do tempo/lead | — | — |

> O **conjunto-ouro de ~30 leads rotulados** é também o principal artefato de avaliação
> acadêmica do trabalho.

## 5. Governança & segurança (ângulo AI Leadership)

- Dados de prospect são confidenciais/PII → **anonimizar** antes de enviar à API quando possível.
- Usar configuração da API que **não usa os dados para treinamento**.
- Registrar **disclaimer**: saída é sugestão, decisão final é humana (human-in-the-loop).
- Documentar riscos: viés, alucinação, vazamento de dados.

## 6. Próximos passos

- [ ] Validar este recorte com o professor/orientador
- [ ] Montar base de cases curada (`data/cases/`)
- [ ] Definir schema JSON da saída do LLM
- [ ] Criar conjunto-ouro de leads rotulados para avaliação
- [ ] Implementar pipeline: ingestão RAG → classificação → UI
