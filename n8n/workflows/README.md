# Workflow N8N — AI SDR (Qualificação de Leads)

[`ai-sdr-qualification.json`](./ai-sdr-qualification.json) implementa o pipeline descrito em
[`docs/mvp-scope.md`](../../docs/mvp-scope.md#3-arquitetura-mínima-proposta):

```
Webhook (domínio) → scraping do site → busca SearXNG → compila perfil de pesquisa
  → embedding (Ollama) → busca cases similares (Qdrant) → monta prompt
  → classifica (Ollama/Gemma, saída estruturada) → monta resposta → responde ao Open WebUI
```

**Já foi importado** no seu N8N local via CLI (`n8n import:workflow`) para validar que a estrutura
é aceita — não precisei da sua senha para isso, o import roda direto no banco do container. Você
vai encontrá-lo como **"AI SDR - Qualificação de Leads"** assim que abrir o N8N.

## O que falta fazer manualmente (não dá para automatizar sem sua senha)

1. Abrir `http://localhost:5678` e completar o **setup inicial do N8N** (criar a conta de owner
   — só você deve definir essa senha).
2. Abrir o workflow **"AI SDR - Qualificação de Leads"** no editor e dar uma olhada nos 11 nodes.
3. Conferir os dois nodes que chamam o Ollama ("Gerar Embedding" e "Classificar com Gemma") —
   os nomes de modelo (`ollama.com/library/embeddinggemma:latest` e `gemma4:12b-mlx`) já batem
   com o que está instalado no seu host, mas confirme se não mudaram.
4. **Ativar** o workflow (toggle no canto superior direito) para o webhook em produção responder.
5. Testar:
   ```bash
   curl -X POST http://localhost:5678/webhook/ai-sdr \
     -H "Content-Type: application/json" \
     -d '{"message": "itau.com.br"}'
   ```

## Limitações conhecidas desta primeira versão

- **Scraping do site do prospect** é um GET simples na home (`https://dominio`) sem JavaScript
  rendering — sites que dependem de SPA/JS podem retornar pouco conteúdo útil. Nesse caso, o
  resultado do SearXNG compensa parcialmente.
- Não há tratamento de erro elaborado: se o site do prospect bloquear o scraping ou o domínio não
  resolver, o node está configurado para não derrubar o workflow (`neverError`), mas o perfil de
  pesquisa ficará mais pobre nesse caso.
- O node de classificação (Gemma) tem timeout de 120s — modelos locais podem ser lentos dependendo
  do hardware; ajuste se necessário.
- Eu **não consegui rodar o workflow ponta a ponta** aqui (executar via CLI conflita com o processo
  do N8N já rodando, e a API exige login que só você pode criar) — validei a estrutura via
  import/export, mas o teste funcional real (passo 5 acima) ainda precisa ser feito por você.

## Function/Pipe do Open WebUI

Ver [`openwebui/pipe_ai_sdr.py`](../../openwebui/pipe_ai_sdr.py) — cole o conteúdo em
Admin Panel → Functions → New Function, habilite, e selecione "AI SDR - Qualificação de Leads"
como modelo no chat.
