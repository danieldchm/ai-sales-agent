# Schema de saída do LLM

Contrato estruturado que o Gemma deve seguir ao classificar um prospect. Fonte única em
[`n8n/schemas/llm-output.schema.json`](../n8n/schemas/llm-output.schema.json).

> **Atualização (2026-07-10):** o parâmetro `format` da API do Ollama (que deveria forçar essa
> estrutura via constrained decoding) é **ignorado por `gemma4:12b-mlx`** — confirmado em teste
> isolado. O schema ainda é a fonte única de verdade, mas é aplicado via **exemplo embutido no
> texto do prompt** (node "Montar Prompt" do workflow) em vez do parâmetro `format`, e o node
> "Montar Resposta Final" faz parsing tolerante (remove blocos ` ``` `, acessa campos com
> fallback). Testado ponta a ponta com sucesso. Ver detalhes em
> [`n8n/workflows/README.md`](../n8n/workflows/README.md#descoberta-importante-format-json-schema-do-ollama-é-ignorado-por-este-modelo).

## Decisão de design: `cases_relevantes` não é gerado pelo LLM

Os cases similares (recuperados do Qdrant) **não** fazem parte deste schema — eles são
recuperados deterministicamente antes da chamada ao LLM e reinseridos na resposta final pelo
próprio workflow (node "Montar Resposta Final"), com o `titulo`, `classificacao_correta` e
`resultado_licao` exatamente como estão em [`data/cases/`](../data/cases/). Isso evita que o
modelo **alucine** um case ou cite errado uma lição que nunca existiu — o LLM decide a
classificação do prospect, mas nunca inventa a citação da fonte.

## Exemplo de saída (preenchido pelo LLM)

```json
{
  "dominio": "itau.com.br",
  "perfil_empresa": {
    "nome": "Itaú Unibanco",
    "setor": "Bancos / Serviços Financeiros",
    "porte_estimado": "Grande",
    "resumo": "Banco de grande porte com iniciativas públicas de modernização digital e vagas ativas para engenharia de dados e ML.",
    "sinais_maturidade_digital": [
      "Vagas abertas para 'Machine Learning Engineer' e 'MLOps'",
      "Notícias recentes sobre parceria com fornecedores de nuvem para IA"
    ]
  },
  "classificacao": {
    "tipo": "BI",
    "confianca": "Média",
    "justificativa": "Os sinais encontrados apontam para modelagem preditiva de risco/crédito (padrão do case Nubank), não para um caso de linguagem natural/GenAI. Recomenda-se confirmar no discovery se a demanda real envolve geração de texto ou apenas scoring."
  },
  "maturidade_ia_prospect": {
    "nivel": "Em desenvolvimento",
    "justificativa": "Já possui equipe própria de dados e IA, mas não há evidência pública de uso de GenAI em produção."
  },
  "direcionamento_estrategia": {
    "recomendacao": "Aprofundar discovery antes de avançar",
    "justificativa": "A pesquisa não é conclusiva sobre se a demanda é geração de texto (GenAI) ou modelagem preditiva (BI) — a primeira reunião de discovery deve fechar essa dúvida antes de dimensionar a proposta."
  },
  "perguntas_discovery": [
    "O resultado final esperado é um texto/conversa gerado, ou um número/decisão (score, previsão)?",
    "Existe histórico de dados rotulados para treinar e validar um modelo supervisionado?",
    "Que parte do processo hoje depende de interpretar linguagem não estruturada?"
  ]
}
```

O workflow então mescla este JSON com os `cases_relevantes` reais do Qdrant e formata tudo como
Markdown para o chat do Open WebUI (ver node "Montar Resposta Final").
