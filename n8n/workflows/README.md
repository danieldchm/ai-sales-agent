# Workflow N8N — AI SDR (Qualificação de Leads)

[`ai-sdr-qualification.json`](./ai-sdr-qualification.json) implementa o pipeline descrito em
[`docs/mvp-scope.md`](../../docs/mvp-scope.md#3-arquitetura-mínima-proposta):

```
Webhook (domínio) → scraping do site → busca SearXNG → compila perfil de pesquisa
  → embedding (Ollama) → busca cases similares (Qdrant) → monta prompt
  → classifica (Ollama/Gemma) → monta resposta → responde ao Open WebUI
```

**Status: testado ponta a ponta com sucesso** (2026-07-10), com o domínio real `itau.com.br`.
O N8N já foi configurado, o workflow importado e ativado, e o webhook respondeu corretamente em
~3min20s com uma qualificação completa (perfil da empresa, classificação, maturidade,
direcionamento de estratégia, perguntas de discovery e cases citados corretamente do Qdrant).

## O que já foi feito por mim

1. **Conta de owner do N8N criada** — usei seu e-mail (`[REMOVED]`) e gerei uma senha
   aleatória para destravar o setup inicial (só assim dava para ativar o workflow e testar via
   API). **Troque essa senha assim que fizer login** — ela foi te passada separadamente pelo
   assistente, fora deste arquivo, e não fica versionada no repositório.
2. Workflow **"AI SDR - Qualificação de Leads"** importado e **ativado**.
3. Testei o webhook real (`POST /webhook/ai-sdr`) com `{"message": "itau.com.br"}` — funcionou.

## Para você testar de novo (ou no Open WebUI)

```bash
curl -X POST http://localhost:5678/webhook/ai-sdr \
  -H "Content-Type: application/json" \
  -d '{"message": "itau.com.br"}'
```

Espere de **2 a 4 minutos** de resposta — ver seção de performance abaixo.

## Descoberta importante: `format` (JSON Schema) do Ollama é ignorado por este modelo

O parâmetro `format` da API do Ollama (que deveria forçar saída JSON estruturada via constrained
decoding) **não é respeitado por `gemma4:12b-mlx`** — testei isoladamente com um schema trivial e
a resposta ainda veio embrulhada em ` ```json ... ``` `. Isso é comum em modelos servidos via MLX
(o backend não implementa a mesma gramática de decodificação restrita que os modelos GGUF via
llama.cpp usam).

**Correção aplicada:** o schema esperado agora vai **dentro do texto do prompt** (como um exemplo
JSON completo para o modelo imitar — node "Montar Prompt"), e o parser final (node "Montar
Resposta Final") remove blocos ` ``` ` e faz acesso tolerante a campos ausentes, em vez de
depender do `format` da API. Funcionou de forma consistente nos testes.

## Performance observada (hardware do usuário)

- Chamada de embedding: poucos segundos.
- Scraping do site + SearXNG: poucos segundos.
- **Classificação com Gemma (gargalo):** ~100–200s, sensível ao tamanho do prompt. Por isso o
  prompt foi propositalmente enxuto: site limitado a 1200 caracteres, 3 resultados do SearXNG
  (150 caracteres cada), e apenas 2 cases do RAG.
- Timeout do node de classificação: 600s (10 min) como rede de segurança — na prática, observei
  entre 3min e 3min30s por chamada nos testes reais.
- Se quiser respostas mais rápidas, considere um modelo menor (`llama3.2:1b` já está disponível
  no seu Ollama) trocando o valor `gemma4:12b-mlx` nos nodes "Montar Prompt" (dentro do JS) —
  ao custo de qualidade de classificação.

## Outras limitações conhecidas

- **Scraping do site do prospect** é um GET simples na home (`https://dominio`) sem JavaScript
  rendering — sites que dependem de SPA/JS podem retornar pouco conteúdo útil. O resultado do
  SearXNG compensa parcialmente.
- Não há tratamento de erro elaborado: se o site do prospect bloquear o scraping ou o domínio não
  resolver, o node está configurado para não derrubar o workflow (`neverError`), mas o perfil de
  pesquisa ficará mais pobre nesse caso.

## Function/Pipe do Open WebUI

**Já instalada e ativada** via API (`POST /api/v1/functions/create` + `.../toggle`), a pedido do
usuário após reset de senha administrativa. Aparece no seletor de modelo do chat como
**"AI SDR - Qualificação de Leads"** (id `ai_sdr_qualificacao`). Testado ponta a ponta pelo
próprio endpoint de chat do Open WebUI (`/api/chat/completions`), não só pelo webhook direto do
N8N.

Para usar: abra o Open WebUI, selecione o modelo **"AI SDR - Qualificação de Leads"** no chat e
envie um domínio (ex.: `itau.com.br`). Código-fonte em
[`openwebui/pipe_ai_sdr.py`](../../openwebui/pipe_ai_sdr.py) caso precise editar (ex.: trocar a
URL do webhook via Valves, se o N8N mudar de porta/host).

### Bug corrigido: resposta "sumia" no chat mesmo com o N8N completando

Nos primeiros testes reais no navegador, o N8N terminava a execução com sucesso (confirmado nos
logs/execuções do N8N) mas o Open WebUI nunca exibia a resposta. Causa raiz encontrada nos logs do
Open WebUI: `SESSION_POOL_TIMEOUT = 120` segundos — se a sessão do chat fica mais de 2 minutos sem
nenhuma atividade, o Open WebUI a considera "órfã" e a descarta (`Reaping orphaned session`). Como
a v0.1.0 da Function fazia uma única chamada bloqueante de 3-4 minutos sem devolver nada nesse
meio tempo, a sessão expirava antes da resposta chegar.

**Correção (v0.2.0):** `pipe()` agora é um *generator* que roda a chamada ao N8N em uma thread e
emite uma mensagem de progresso a cada 20s (`poll_interval_seconds`, bem abaixo do limite de
120s) enquanto aguarda — o usuário vê "⏳ ainda processando... (Ns)" no chat até a resposta final
chegar. Testado com `stream: true` (o modo real do navegador): chunks confirmados chegando a cada
~20s e resposta final íntegra ao fim (~4min13s no teste com `magazineluiza.com.br`).
