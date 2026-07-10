"""
title: AI SDR - Qualificação de Leads
author: ai-sales-agent
version: 0.1.0
description: Envia a mensagem do vendedor (contendo o domínio do prospect) para o workflow N8N de qualificação (research + RAG + Ollama) e retorna a recomendação formatada no chat.
"""
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

    def __init__(self):
        self.id = "ai_sdr_qualificacao"
        self.name = "AI SDR - Qualificação de Leads"
        self.valves = self.Valves()

    def pipe(self, body: dict) -> str:
        messages = body.get("messages", [])
        user_message = next(
            (m.get("content", "") for m in reversed(messages) if m.get("role") == "user"),
            "",
        )

        if not user_message.strip():
            return "Envie o domínio do prospect (ex.: `itau.com.br`) para iniciar a qualificação."

        try:
            resp = requests.post(
                self.valves.n8n_webhook_url,
                json={"message": user_message},
                timeout=self.valves.timeout_seconds,
            )
            resp.raise_for_status()
        except requests.exceptions.RequestException as e:
            return f"⚠️ Erro ao chamar o workflow do N8N ({self.valves.n8n_webhook_url}): {e}"

        try:
            data = resp.json()
        except ValueError:
            return f"⚠️ O N8N respondeu, mas não em JSON:\n\n{resp.text}"

        return data.get("response", "⚠️ O workflow respondeu, mas sem o campo 'response' esperado.")
