# Workflow N8N — AI SDR (Qualificação de Leads)

[`ai-sdr-qualification.json`](./ai-sdr-qualification.json) implementa o pipeline descrito em
[`docs/mvp-scope.md`](../../docs/mvp-scope.md#3-arquitetura-mínima-proposta):

```
Chat (n8n) → scraping do site → detecta setor + monta queries
  → busca SearXNG (empresa) → busca SearXNG (setor) → busca SearXNG (mercado)
  → compila perfil de pesquisa → embedding (Ollama) → busca cases similares (Qdrant)
  → monta prompt → classifica (Chain + memória por sessão) → monta resposta → chat (n8n)
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

## Para você testar de novo

Abra o workflow no editor do n8n e clique em **"Chat"** (botão no canto inferior, disponível porque
o trigger é o node nativo **"Chat - Recebe Prompt"**). Digite o domínio do prospect, com contexto
opcional, ex.: `itau.com.br - prospect quer automatizar atendimento do call center`. Mensagens
seguintes na mesma janela de chat reaproveitam a mesma sessão (memória por sessão — ver seção
abaixo).

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

## Atualização (2026-07-12): contexto do vendedor era ignorado + memória por sessão

**Bug corrigido:** o node "Extrair Domínio" só extraía o domínio da mensagem via regex e
descartava todo o resto do texto. Se o vendedor escrevesse, por exemplo,
`itau.com.br - prospect quer automatizar atendimento do call center`, o trecho depois do domínio
nunca chegava ao LLM. Agora esse texto é preservado como `contexto_usuario`, propagado pelos nodes
"Compilar Perfil de Pesquisa" → "Montar Prompt" e injetado explicitamente no prompt final sob o
título "CONTEXTO INFORMADO PELO VENDEDOR", com instrução para o modelo não ignorá-lo.

**Memória por sessão adicionada:** o node de classificação foi trocado de uma chamada HTTP crua ao
Ollama para os nodes nativos do n8n (`n8n-nodes-langchain`): **"Ollama Chat Model"** +
**"Memória por Sessão"** (Window Buffer Memory, últimas 6 interações) + **"Classificar com Gemma
(Chain)"** (Basic LLM Chain). A chave de sessão (`sessionKey`) vem do `sessionId` gerado
automaticamente pelo node de chat nativo do n8n — cada janela/aba de chat tem sua própria memória.

**Credencial do Ollama:** criada via API do n8n (`ollamaApi`, base URL
`http://host.docker.internal:11434`) e já wireada no node "Ollama Chat Model".

**Nota de tipo de node:** o pacote instalado é `@n8n/n8n-nodes-langchain` (com esse prefixo
completo, não apenas `n8n-nodes-langchain`) — os 4 nodes novos (`chatTrigger`, `chainLlm`,
`lmChatOllama`, `memoryBufferWindow`) usam esse prefixo no JSON do workflow.

**Status: testado ponta a ponta com sucesso** (2026-07-12), via `POST` direto no webhook do node de
Chat (`/webhook/<webhookId>/chat`, `{"chatInput": ..., "sessionId": ...}`):
- `itau.com.br` (sem contexto extra) → classificado corretamente como GenAI real, confiança Alta.
- `magazineluiza.com.br - o prospect quer um chatbot para recomendar produtos, mas suspeito que
  seja só um motor de regras` → o modelo usou explicitamente a suspeita do vendedor na
  justificativa, classificando como Automação clássica com confiança Baixa. Confirma que o bug do
  contexto perdido foi corrigido.

## Atualização (2026-07-12): pesquisa "deep research" (empresa + setor + mercado)

Antes o research era só scraping do site + **uma** busca genérica no SearXNG
(`"<domínio> empresa notícias tecnologia inteligência artificial"`). Isso não dava sinal
suficiente sobre o setor/indústria do prospect para embasar o `direcionamento_estrategia` — só
sobre a empresa em si.

**Mudança:** novo node **"Detectar Setor e Montar Queries"** (logo após o scraping do site) faz
uma heurística simples (contagem de palavras-chave em português no texto do site) para adivinhar
o setor do prospect (bancário, varejo, saúde, seguros, indústria, logística, educação, jurídico,
agronegócio, telecom, tecnologia — ou "Indeterminado" se nada bater). A partir disso, 3 buscas
sequenciais no SearXNG substituem a única busca anterior:

1. **"Buscar no SearXNG (Empresa)"** — notícias/sinais da empresa (query igual à anterior).
2. **"Buscar no SearXNG (Setor)"** — tendências de IA e automação no setor detectado (nova).
3. **"Buscar no SearXNG (Mercado)"** — concorrentes e posicionamento de mercado (nova).

O node **"Compilar Perfil de Pesquisa"** agora junta os 3 resultados em seções separadas do
`perfil_pesquisa`, e o prompt (node "Montar Prompt") instrui explicitamente o modelo a usar os
sinais de setor/mercado para embasar `direcionamento_estrategia` e `perguntas_discovery`, não só
o site institucional.

**Sobre a heurística de setor:** é só contagem de palavras-chave, não é confiável sozinha — por
isso o texto do prompt avisa o modelo para "tratar com ceticismo se parecer errado". Serve para
direcionar a segunda busca, não como classificação final (essa continua sendo responsabilidade do
LLM, com base em toda a pesquisa).

**Trade-off de performance:** mais 2 chamadas ao SearXNG (segundos, não é o gargalo) e mais texto
no prompt final (~8 resultados de busca em vez de 3) — o que pode aumentar um pouco o tempo de
classificação do Gemma (já o gargalo do pipeline, ver seção de performance acima). Se ficar lento
demais, reduza os `.slice(n)` no node "Compilar Perfil de Pesquisa" (atualmente 3+3+2).

**Status: testado ponta a ponta com sucesso** (2026-07-12) com `nubank.com.br` via webhook do chat.
A resposta trouxe sinais que dificilmente viriam só do scraping do site institucional (ex.: uso de
IA Generativa nos canais de atendimento via App/WhatsApp para Pix, programa interno "Vale IA" de
incentivo ao uso de LLMs pelos funcionários) — evidência de que as buscas de setor/mercado estão
de fato agregando contexto além do site, e o modelo usou isso para embasar tanto a classificação
(GenAI real, confiança Alta) quanto o direcionamento ("Aprofundar discovery", com perguntas sobre
segurança e alucinação em transações financeiras via Pix).

## Atualização (2026-07-12): relatórios de RI/mercado para empresas negociadas na B3

Nova sub-seção do pipeline, em paralelo à pesquisa web: quando o prospect é identificado como uma
empresa negociada na **B3** (bolsa brasileira — escopo intencionalmente restrito ao Brasil, sem
cobertura de bolsas dos EUA), o workflow busca os relatórios de resultados/RI mais recentes em PDF,
extrai o texto, divide em chunks, gera embeddings e faz upload para uma coleção própria no Qdrant
(`ai_sdr_relatorios_financeiros`), separada da base de cases. Os trechos mais relevantes desses
relatórios são recuperados depois (mesma lógica de RAG já usada para os cases) e injetados no prompt
final, na mesma posição em que a pesquisa web é usada — o LLM é instruído a priorizar esses dados
oficiais para classificação, maturidade e direcionamento de estratégia quando disponíveis.

**Novos nodes:** `Extrair Nome da Empresa e CNPJ` → `Consultar CNPJ (BrasilAPI)` → `Buscar Tickers B3
(brapi)` → `Identificar Empresa Listada (B3)` → `Garantir Collection Financeira Existe` → `IF Empresa
Listada na B3?` → (verdadeiro) `Buscar Release de Resultados (SearXNG)` → `Selecionar Últimos 3 PDFs`
→ `Baixar Relatório PDF` → `Extrair Texto do Relatório` → `Limpar e Dividir em Chunks` → `Gerar
Embedding (Chunk Financeiro)` → `Montar Corpo do Upsert (Financeiro)` → `Upsert Chunk Financeiro
(Qdrant)`; (falso) `Sem Documentos Financeiros`. Os dois lados convergem em `Merge Status Financeiro`
→ `Finalizar Status Financeiro`, que força o upload a terminar antes de `Compilar Perfil de Pesquisa`
prosseguir. Depois, `Buscar Trechos de Relatórios (Qdrant)` reaproveita o mesmo embedding já calculado
para a busca de cases, evitando uma chamada extra ao Ollama.

**Bugs encontrados e corrigidos (todos ainda válidos, mesmo após a migração para CVM abaixo):**
1. `$('Node').item.json` (usado em vários nodes do workflow, não só os novos) depende do rastreamento
   de *paired item* do n8n, que quebra quando um node "explode" 1 item em N (o node de chunking) e
   depois os fluxos convergem de novo via `Merge`. Corrigido globalmente (18 ocorrências em 9 nodes)
   trocando por `$('Node').first().json`, que lê a saída do node diretamente sem depender desse
   rastreamento — correto aqui porque todo node deste pipeline produz no máximo 1 item relevante no
   ponto em que é referenciado.
2. **Falso positivo** (achado testando `airbnb.com`): "XP INC." normaliza para só "XP" (2 caracteres,
   depois de remover o sufixo societário "INC") e "XP" aparecia como substring dentro de "EXPERIENCES"
   (do título "...Unique Homes & Experiences" do site da Airbnb) — batendo incorretamente com o ticker
   `XPBR31`. Corrigido trocando a comparação de substring bruta por comparação de **token (palavra
   inteira)**: "XP" não é a mesma palavra que "EXPERIENCES", então não bate mais. Uma primeira tentativa
   de correção (exigir um tamanho mínimo de 4 caracteres) causou uma **regressão real** — bloqueou o
   match legítimo de "WEG" (3 letras) — corrigida com a comparação por token, que resolve os dois casos.

## Atualização (2026-07-13): migração da busca de PDFs para dados oficiais da CVM

**Problema reportado pelo usuário:** testando `weg.net`, o workflow travava com
`Invalid URL: about:blank. URL must start with "http" or "https"`. Investigando, ficou claro que a
abordagem anterior (buscar PDFs de resultados via SearXNG) tinha um problema estrutural, não só esse
bug pontual: os relatórios reais de RI de várias empresas B3 (WEG incluída) ficam hospedados atrás de
um **widget JS autenticado** (a plataforma MZIQ, usada por dezenas de companhias abertas brasileiras),
que não é rastreável por scraping simples nem indexado por motores de busca — confirmado testando
`site:ri.weg.net filetype:pdf`, que só trouxe apresentações antigas (slides de 2018/2022), nunca os
releases trimestrais reais.

**Decisão (aprovada pelo usuário):** substituir a busca via SearXNG por **dados abertos oficiais da
CVM** (Comissão de Valores Mobiliários — reguladora do mercado de capitais brasileiro), que são
públicos, estruturados e não exigem autenticação. Trade-off aceito conscientemente: os dados vêm em
formato de linhas de balanço/DRE (não um texto corrido de "release"), e a integração é mais complexa
(download de ZIPs anuais de ~10MB que descompactam para ~240MB, contendo 19 arquivos por ano).

**Novo desenho do pipeline** (substitui inteiramente `Buscar Release de Resultados (SearXNG)` →
`Selecionar Últimos 3 PDFs` → `IF URL Válida?` → `Baixar Relatório PDF` → `Extrair Texto do Relatório`):

1. `Buscar Cadastro CVM (Cia Aberta)` — baixa o [cadastro público de companhias
   abertas](https://dados.cvm.gov.br/dados/CIA_ABERTA/CAD/DADOS/cad_cia_aberta.csv) (CSV, ~1.5MB).
2. `Identificar CD_CVM` — casa o CNPJ extraído do site (match exato) ou o nome da empresa (mesma lógica
   de token já usada no match B3) contra esse cadastro, obtendo o `CD_CVM` (código de registro na CVM,
   necessário para filtrar os arquivos seguintes) com zero-padding para 6 dígitos (o cadastro usa "5410"
   sem padding, os arquivos de ITR usam "005410" — descoberto inspecionando os dados reais).
3. `Baixar ITR CVM (Ano Atual)` + `Baixar ITR CVM (Ano Anterior)` — baixam os ZIPs anuais de
   [Informações Trimestrais](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/ITR/DADOS/) do ano corrente e
   do anterior (o ano corrente sozinho normalmente só tem 1 trimestre arquivado; os dois juntos garantem
   pelo menos 3-4 trimestres disponíveis).
4. `Descompactar ITR (Ano Atual)` + `Descompactar ITR (Ano Anterior)` — node nativo `Compression` do n8n
   (limite padrão de 2GB/5000 entradas, então os ~240MB descompactados não são um problema).
5. `Merge ITR Descompactados` → `Limpar e Dividir em Chunks` (nome do node reaproveitado do desenho
   anterior) — encontra, entre os 19 arquivos descompactados, o `itr_cia_aberta_DRE_con_{ano}.csv`
   (Demonstração do Resultado **Consolidado** — testado e confirmado que o individual, "_ind_", vem
   zerado para holdings como a WEG, já que a operação real está nas subsidiárias), filtra pelas linhas
   do `CD_CVM` alvo com `ORDEM_EXERC = 'ÚLTIMO'` (evita duplicar a coluna de comparação do ano anterior
   que a própria CVM já inclui em cada linha), agrupa por período (`DT_REFER`) e mantém os 3 mais
   recentes, formatando cada um como texto (conta + descrição + valor em R$ mil).
6. Segue o mesmo pipeline de sempre: `Gerar Embedding (Chunk Financeiro)` → `Montar Corpo do Upsert
   (Financeiro)` → `Upsert Chunk Financeiro (Qdrant)` → `Finalizar Status Financeiro` → retrieval via
   `Buscar Trechos de Relatórios (Qdrant)` → `Montar Prompt`.

**Bug encontrado e corrigido durante o teste ao vivo (`weg.net`):** a primeira versão lia o binário do
CSV descompactado com `Buffer.from(item.binary[chave].data, 'base64')` — isso **falha silenciosamente**
(não dá erro, só produz lixo) quando o n8n está em modo de armazenamento binário filesystem/S3 em vez de
memória, o que é plausível/comum para arquivos deste tamanho. Resultado: 0 chunks encontrados mesmo com
os dados reais existindo (confirmado inspecionando os CSVs manualmente). Corrigido usando o helper
oficial do n8n, `await this.helpers.getBinaryDataBuffer(itemIndex, chave)`, que funciona
independentemente do modo de armazenamento — verificado com um workflow de teste isolado antes de
aplicar a correção.

**Status: testado e funcionando ponta a ponta com `weg.net`** — CD_CVM `005410` corretamente resolvido
via match de nome (CNPJ não encontrado no site desta vez), 10 chunks reais extraídos de 3 períodos
(2026-03-31, 2025-09-30 e mais um), com valores reais como "Receitas Financeiras: R$ 461.720 mil". A
resposta final do modelo citou explicitamente "Receita de Venda de Bens e/ou Serviços de R$ 30.5 bilhões
em 2025-09-30" — confirma que os dados oficiais da CVM chegaram ao prompt e influenciaram a análise.

**Fontes de dados usadas agora:**
- [`brapi.dev`](https://brapi.dev/api/quote/list) — lista gratuita (sem token) de ~2000 tickers da B3,
  usada para casar o nome do prospect com um ticker.
- [`brasilapi.com.br`](https://brasilapi.com.br/api/cnpj/v1/) — consulta de CNPJ (Receita Federal) para
  obter a razão social oficial. **Nota:** a BrasilAPI não tem endpoint de tickers/empresas listadas nem
  de dados financeiros — só é usada pela consulta de CNPJ.
- [`dados.cvm.gov.br`](https://dados.cvm.gov.br/) — cadastro de companhias abertas + Informações
  Trimestrais (ITR), dados oficiais, públicos, sem autenticação.

**Limitações conhecidas (não resolvidas, por design):**
- **Heurística de nome é best-effort.** Apelidos de marketing sem sobreposição textual com a razão
  social (ex.: "Nubank" vs. "Nu Holdings Ltd.") não são encontrados. A consulta de CNPJ mitiga isso
  parcialmente, mas depende do CNPJ estar no rodapé do site e do site não bloquear scraping simples.
- **Só B3.** Sem cobertura de bolsas dos EUA (fora do escopo, por pedido explícito do usuário).
- **Só Demonstração do Resultado (DRE) Consolidado, só ITR (trimestral).** Não inclui balanço
  patrimonial, fluxo de caixa, ou a DFP anual (Q4) — poderia ser estendido buscando outros arquivos do
  mesmo ZIP (ex.: `BPA_con`, `BPP_con`) com a mesma lógica de extração já implementada.
- **Coleção do Qdrant cresce sem limite** entre análises — os IDs dos pontos são determinísticos (hash
  de `domínio|período|índice do chunk`), então reanalisar a mesma empresa sobrescreve em vez de
  duplicar, mas não há limpeza de empresas antigas/não relacionadas.
- **Latência adicional**: dois downloads de ~10-30MB + descompactação de ~240MB + até ~10 chamadas
  extras de embedding, quando uma empresa é identificada como listada.

## Atualização (2026-07-13): troca do LLM de classificação — Ollama/Gemma local → Google Gemini

A pedido do usuário ("atualizei o modelo para utilizar o gemini 3.5 flash, utilize-o no lugar do ollama
por enquanto"), o node de classificação passou a usar a **API do Google Gemini** em vez do Ollama local.

**O que mudou:** o node `Ollama Chat Model` foi substituído por `Gemini Chat Model`
(`@n8n/n8n-nodes-langchain.lmChatGoogleGemini`), usando a credencial `googlePalmApi` que o próprio
usuário já havia criado no n8n (`Google Gemini(PaLM) Api account`). O node `Classificar com Gemma
(Chain)` foi renomeado para `Classificar com Gemini (Chain)` para refletir a troca (nenhuma mudança de
lógica, só o LLM conectado). Modelo configurado: `models/gemini-2.5-flash` — **nota:** "gemini 3.5
flash" não corresponde a nenhuma string de modelo reconhecida pelo node no momento da configuração;
usei o default documentado do node como ponto de partida. Se o usuário quis dizer uma versão específica
diferente (ex.: `models/gemini-3-flash` ou outra), é só trocar o parâmetro `modelName` no node.

**Cuidado detectado:** durante essa troca, uma execução concorrente (rodada pelo próprio usuário
diretamente na UI do n8n, com um node próprio chamado "Google Gemini Chat Model") revelou que o usuário
estava editando o workflow pela UI em paralelo às mudanças feitas via API nesta sessão. Como os pushes
via API substituem a definição inteira do workflow a partir de um arquivo local (sem mesclar com
mudanças feitas na UI), há risco de um `PUT` sobrescrever edições manuais concorrentes. Nesta sessão
isso foi resolvido reaplicando a troca de LLM de forma equivalente (reaproveitando a credencial que o
usuário já tinha criado), mas vale ter em mente: **evitar editar o workflow pela UI do n8n enquanto
mudanças estiverem sendo aplicadas via API na mesma sessão**, para não haver conflito.

**Resultado:** tempo de execução ponta a ponta caiu de ~3-4 minutos (Gemma local via Ollama) para
**~38 segundos** (Gemini via API) no teste com `weg.net` — melhoria substancial de latência, ao custo
de depender de uma API externa (deixa de ser 100% local) e do uso ficar sujeito à cota/custo da API do
Gemini.

## Atualização (2026-07-13): upload manual de relatórios PDF (mecanismo paralelo)

Novo ponto de entrada no mesmo workflow, **totalmente independente do chat principal**: um formulário
para enviar manualmente um relatório de RI/mercado em PDF (ex.: baixado à mão do site da empresa,
contornando a limitação de busca automática documentada acima), que é processado e indexado na mesma
collection do Qdrant (`ai_sdr_relatorios_financeiros`) usada pelos dados da CVM — a próxima análise
daquele domínio no chat principal já recupera esse conteúdo junto com o resto.

**Como usar:** acesse `http://localhost:5678/form/fb20b002-0000-4000-8000-000000000001` (ou clique em
"Chat"/"Test" a partir do node "Upload Manual de Relatório PDF" no editor do n8n), preencha domínio,
ticker (opcional), título do documento e selecione o PDF.

**Novos nodes:** `Upload Manual de Relatório PDF` (Form Trigger) → `Extrair Texto do PDF Enviado`
(`extractFromFile`, PDF) → `IF Extração Bem-Sucedida?` → (verdadeiro) `Garantir Collection Financeira
Existe (Upload)` → `Preparar Chunks do Upload Manual` → `Gerar Embedding (Chunk Manual)` → `Montar
Corpo do Upsert (Manual)` → `Upsert Chunk Manual (Qdrant)` → `Resumir Upload Concluído` → `Upload
Concluído (Sucesso)` (form de conclusão); (falso) `Upload Falhou (Erro)` (form de conclusão explicando
o problema — PDF corrompido, protegido por senha ou sem texto selecionável).

**Dois bugs reais encontrados e corrigidos durante o teste ao vivo** (upload de um PDF real de 20
páginas, [balanço do Itaú](https://static.poder360.com.br/2025/08/itau-2-tri-balanco-2025.pdf)):

1. **Perda de dados binários por node HTTP no meio do caminho.** O desenho original tinha `Garantir
   Collection Financeira Existe (Upload)` entre o Form Trigger e `Extrair Texto do PDF Enviado` — como
   todo node HTTP Request deste workflow, ele substitui o item inteiro (json *e* binário) pela resposta
   da própria chamada, então o PDF enviado desaparecia antes de chegar no node de extração
   (`"none was found"` no binary `arquivo_pdf`). Corrigido reordenando: o Form Trigger vai direto para
   `Extrair Texto do PDF Enviado`, e o check de collection passou para depois do `IF`, no ramo
   verdadeiro (não depende de binário, só precisa rodar antes do upsert).
2. **Mesmo problema, mas com o texto extraído.** Ao mover o node de collection para o ramo verdadeiro,
   ele passou a ficar *antes* de `Preparar Chunks do Upload Manual` — que lia `$json.text` diretamente,
   e esse `$json` já não era mais a saída de `Extrair Texto do PDF Enviado` (era a resposta do PUT no
   Qdrant). Resultado: 0 chunks gerados silenciosamente (sem erro), e a execução ficava presa para
   sempre em status "waiting" (nunca chegava no form de conclusão, porque não havia itens para
   processar). Corrigido trocando para `$('Extrair Texto do PDF Enviado').first().json.text` — mesma
   categoria de bug (e mesma correção) já documentada nos outros nodes deste workflow que ficam
   depois de uma chamada HTTP no meio do fluxo.

**Descoberta sobre o protocolo do Form Trigger do n8n** (relevante só para quem for testar via
`curl`/script em vez do navegador): os campos do formulário **não** são submetidos pelo `fieldName`
configurado no node — o multipart precisa usar chaves posicionais `field-0`, `field-1`, `field-2`,
`field-3` (na ordem em que os campos foram definidos), que o n8n internamente traduz de volta para o
`fieldName` de cada campo. Confirmado lendo o código-fonte do node (`Form/utils/utils.js`). Isso não
afeta o uso normal pelo navegador (o HTML gerado pelo próprio n8n já usa esses nomes automaticamente),
só é uma pegadinha ao automatizar o teste via requisição HTTP crua.

**Status: testado e funcionando ponta a ponta** — PDF de 20 páginas processado em 18 chunks reais,
upados corretamente no Qdrant com a metadata certa (domínio, ticker, título), e o form de conclusão
mostrou a mensagem de sucesso com a contagem correta de chunks.

**Limitação conhecida:** point IDs são determinísticos por `domínio|upload-manual|título do
documento|índice do chunk` — reenviar o mesmo PDF com o mesmo título sobrescreve em vez de duplicar,
mas títulos diferentes para o mesmo documento (ou o mesmo título para documentos diferentes) geram
entradas duplicadas/conflitantes na base. Vale manter uma convenção de nomes ao usar o upload manual.

**Confirmado com upload real do usuário:** relatório anual da Gerdau (`relatorio-anual-gerdau-2025-pt.pdf`,
19,4MB, domínio `gerdau.com.br`, ticker `GGBR4`) — extraído e indexado em 20 chunks reais, confirmados
diretamente no Qdrant com o texto e metadata corretos.

## Atualização (2026-07-13): verificação de relatórios manuais como caminho paralelo à CVM

A pedido do usuário, o pipeline de qualificação (não só o mecanismo de upload) agora **verifica
explicitamente** se já existem relatórios enviados manualmente para o domínio sendo analisado, como um
caminho **paralelo** à validação de dados da CVM — os dois rodam lado a lado dentro do mesmo ramo
"empresa listada na B3", e o status final combina os dois.

**Novos nodes**, ambos ligados diretamente na saída verdadeira de `IF Empresa Listada na B3?` (em
paralelo com `Buscar Cadastro CVM (Cia Aberta)`, não em série):
- `Montar Consulta de Relatórios Manuais` (code) — monta o corpo da consulta ao Qdrant.
- `Verificar Relatórios Manuais Enviados` (http) — `POST .../points/scroll` filtrando por `dominio` +
  `fonte: upload_manual` na collection `ai_sdr_relatorios_financeiros`.

O resultado converge em `Merge Status Financeiro` (agora com 3 entradas em vez de 2: não-listada,
dados da CVM, relatórios manuais) e `Finalizar Status Financeiro` foi atualizado para relatar as duas
fontes juntas — ex.: *"Disponível para esta análise: dados oficiais da CVM... de 3 período(s); e 1
relatório(s) enviado(s) manualmente (relatorio-anual-gerdau-2025-pt.pdf)"*.

**Bug corrigido antes mesmo de testar ao vivo** (mesma categoria já vista várias vezes neste workflow):
`Montar Consulta de Relatórios Manuais` inicialmente lia `$json.dominio` diretamente, mas seu input
direto vem de `Garantir Collection Financeira Existe` (um node HTTP que substitui o json do item pela
própria resposta) — corrigido referenciando `$('Identificar Empresa Listada (B3)').first().json.dominio`
em vez do `$json` direto.

**Nota de escopo:** esse caminho de verificação só roda para empresas identificadas como listadas na
B3 (por pedido explícito do usuário, "para empresas negociadas na bolsa") — mas o retrieval final
(`Buscar Trechos de Relatórios (Qdrant)`, que roda depois, no fluxo principal) já busca por qualquer
conteúdo indexado para o domínio independente de `listada_b3`, então um relatório enviado manualmente
para uma empresa que a heurística de B3 não reconheceu ainda seria recuperado na análise final — só não
aparece explicitamente no `contexto_financeiro_status` da CVM.

**Status: testado e funcionando ponta a ponta** com `gerdau.com.br` — a mesma execução encontrou os 3
períodos de dados da CVM *e* o relatório enviado manualmente pelo usuário momentos antes, e a análise
final citou sinais específicos do relatório anual (plataforma "Gerdau Intelligence", investimento de
R$ 6,1 bilhões em 2025) na classificação e na maturidade em IA.

## Outras limitações conhecidas

- **Scraping do site do prospect** é um GET simples na home (`https://dominio`) sem JavaScript
  rendering — sites que dependem de SPA/JS podem retornar pouco conteúdo útil. O resultado do
  SearXNG compensa parcialmente.
- Não há tratamento de erro elaborado: se o site do prospect bloquear o scraping ou o domínio não
  resolver, o node está configurado para não derrubar o workflow (`neverError`), mas o perfil de
  pesquisa ficará mais pobre nesse caso.

## Open WebUI removido do processo (2026-07-12)

O fluxo antes passava por uma Function/Pipe do Open WebUI (`openwebui/pipe_ai_sdr.py`), que
chamava o webhook do N8N e fazia polling para contornar o `SESSION_POOL_TIMEOUT` do Open WebUI (a
sessão do chat era descartada se ficasse mais de 120s sem retorno, e a classificação leva
3-4min). Essa camada foi **removida** — o arquivo não existe mais no repositório.

Agora o trigger do workflow é o node nativo de chat do n8n ("Chat - Recebe Prompt"), que também
resolve o problema de sessão órfã por natureza (o próprio n8n mantém a conexão do chat aberta
enquanto a execução roda). Use o botão "Chat" no editor do workflow para testar — ver seção acima.
