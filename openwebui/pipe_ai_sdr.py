"""
title: AI SDR - Qualificação de Leads
author: ai-sales-agent
version: 0.2.0
description: Envia a mensagem do vendedor (contendo o domínio do prospect) para o workflow N8N de qualificação (research + RAG + Ollama) e retorna a recomendação formatada no chat.
"""
import threading
import time

import requests
from pydantic import BaseModel, Field


class Pipe:
    class Valves(BaseModel):
        n8n_webhook_url: str = Field(
            default="http://host.docker.internal:5678/webhook/ai-sdr",
            description="URL do webhook do workflow 'AI SDR - Qualificação de Leads' no N8N.",
        )
        timeout_seconds: int = Field(
            default=630,
            description="Timeout (segundos) para aguardar o workflow do N8N responder. Deve ser maior que o timeout do node de classificacao no N8N (600s) -- geracao local do Gemma costuma levar 3-4 minutos.",
        )
        poll_interval_seconds: int = Field(
            default=20,
            description="Intervalo entre atualizacoes de status enquanto aguarda o N8N. Precisa ficar bem abaixo de SESSION_POOL_TIMEOUT (120s) do Open WebUI: uma chamada bloqueante sem nenhum retorno por minutos faz o socket da sessao ser considerado 'orfao' e a resposta final se perde -- foi o bug observado antes desta correcao.",
        )

    def __init__(self):
        self.id = "ai_sdr_qualificacao"
        self.name = "AI SDR - Qualificação de Leads"
        self.valves = self.Valves()

    def pipe(self, body: dict):
        messages = body.get("messages", [])
        user_message = next(
            (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
            "",
        )

        if not user_message.strip():
            yield "Envie o domínio do prospect (ex.: `itau.com.br`) para iniciar a qualificação."
            return

        result = {}

        def call_n8n():
            try:
                resp = requests.post(
                    self.valves.n8n_webhook_url,
                    json={"message": user_message},
                    timeout=self.valves.timeout_seconds,
                )
                resp.raise_for_status()
                result["resp"] = resp
            except requests.exceptions.RequestException as e:
                result["error"] = e

        thread = threading.Thread(target=call_n8n, daemon=True)
        started_at = time.time()
        thread.start()

        yield "🔎 Pesquisando o prospect e consultando o agente (costuma levar de 2 a 4 minutos)...\n"
        while thread.is_alive():
            thread.join(timeout=self.valves.poll_interval_seconds)
            if thread.is_alive():
                elapsed = int(time.time() - started_at)
                yield f"⏳ ainda processando... ({elapsed}s)\n"

        if "error" in result:
            yield f"\n⚠️ Erro ao chamar o workflow do N8N ({self.valves.n8n_webhook_url}): {result['error']}"
            return

        resp = result["resp"]
        try:
            data = resp.json()
        except ValueError:
            yield f"\n⚠️ O N8N respondeu, mas não em JSON:\n\n{resp.text}"
            return

        yield "\n\n" + data.get(
            "response", "⚠️ O workflow respondeu, mas sem o campo 'response' esperado."
        )
