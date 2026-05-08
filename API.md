# API de Foco e Produtividade

Backend em Python com FastAPI para registrar sessões de foco e gerar diagnóstico inteligente de produtividade com insights por categoria.

## Stack
- Python 3.x
- FastAPI
- SQLite
- Pytest

## Arquitetura
- `app/main.py`: camada HTTP (rotas e contrato da API)
- `app/service.py`: regras de negócio (diagnóstico, feedback e insights)
- `app/repository.py`: persistência SQLite
- `app/schemas.py`: validação e serialização (Pydantic)
- `app/database.py`: conexão e bootstrap do banco

Separação aplicada: rota delega para serviço, serviço delega para repositório.

## Instalação
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Execução
```bash
uvicorn app.main:app --reload
```

API em `http://127.0.0.1:8000`.
Documentação automática em `http://127.0.0.1:8000/docs`.

## Endpoints

Header obrigatório em todas as rotas:
- `X-User-Id`: identificador único anônimo do usuário (ex.: UUID)

### POST `/registro-foco`
Cria um registro de sessão.

Payload:
```json
{
  "nivel_foco": 5,
  "tempo_minutos": 50,
  "comentario": "Implementação de endpoint",
  "categoria": "coding"
}
```

Regras:
- `nivel_foco`: inteiro de 1 a 5
- `tempo_minutos`: inteiro maior que 0
- `comentario`: string não vazia
- `categoria`: opcional, default `geral`

Resposta `201`:
```json
{
  "id": 1,
  "user_id": "4d2a8f7c-13b9-4e9c-8f76-5a2818c8f3e2",
  "nivel_foco": 5,
  "tempo_minutos": 50,
  "comentario": "Implementação de endpoint",
  "categoria": "coding",
  "criado_em": "2026-05-07T20:30:00"
}
```

### GET `/diagnostico-produtividade`
Retorna resumo global e insights por categoria.

Resposta `200`:
```json
{
  "media_nivel_foco": 3.67,
  "tempo_total_focado": 135,
  "mensagem_feedback": "Produtividade estável. Pequenos ajustes de ambiente podem elevar seu foco.",
  "insights_por_categoria": [
    {
      "categoria": "coding",
      "media_foco": 4.5,
      "tempo_total": 105,
      "recomendacao": "Excelente desempenho; mantenha esse padrão de execução."
    },
    {
      "categoria": "reuniao",
      "media_foco": 2.0,
      "tempo_total": 30,
      "recomendacao": "Blocos menores e menos interrupções podem ajudar nesta categoria."
    }
  ]
}
```

Base vazia:
- `media_nivel_foco = 0.0`
- `tempo_total_focado = 0`
- `insights_por_categoria = []`
- mensagem orientando iniciar registros

## Lógica de Feedback
- média `< 3.0`: foco baixo, sugerir pausas e menos notificações
- média `3.0 a 4.0`: produtividade estável com ajuste fino
- média `> 4.0`: alto desempenho sustentado

## Tratamento de Erros
- `422`: payload inválido (tipos/ranges/campos vazios)
- `500`: falhas inesperadas

### GET `/dashboard-produtividade`
Retorna dashboard analítico por período com score, alerta de queda e ações recomendadas.

Query params:
- `from` (opcional): data ISO `YYYY-MM-DD`
- `to` (opcional): data ISO `YYYY-MM-DD`

Regras:
- timezone configurável por variável de ambiente `DASHBOARD_TIMEZONE`
- fallback de timezone: `America/Sao_Paulo` (quando variável ausente ou inválida)
- se `from`/`to` ausentes: usa o dia atual local (`from=to=today`)
- `from` deve ser menor ou igual a `to` (`422` se inválido)

Exemplo de configuração:
```bash
export DASHBOARD_TIMEZONE=UTC
uvicorn app.main:app --reload
```

Resposta `200`:
```json
{
  "periodo": {
    "from": "2026-05-01",
    "to": "2026-05-07",
    "timezone": "America/Sao_Paulo"
  },
  "resumo": {
    "sessoes_total": 4,
    "tempo_total_focado": 120,
    "media_nivel_foco": 3.25
  },
  "score_consistencia": 74.2,
  "alerta_queda_foco": {
    "status": true,
    "variacao_percentual": -40.0,
    "mensagem": "Queda de foco detectada no período recente; revise interrupções e tamanho dos blocos."
  },
  "top_categoria": {
    "categoria": "coding",
    "media_foco": 5.0,
    "tempo_total": 60
  },
  "categoria_em_risco": {
    "categoria": "reuniao",
    "media_foco": 1.5,
    "tempo_total": 60
  },
  "streak_dias": 4,
  "faixas_de_ouro": [
    "09:00-11:59",
    "15:00-17:59"
  ],
  "comparativo_periodo_anterior": {
    "media_nivel_foco_delta": 0.75,
    "tempo_total_focado_delta": 45,
    "sessoes_total_delta": 2
  },
  "acoes_recomendadas": [
    "Defina horário fixo diário para sessões de foco e reduza variações de rotina.",
    "Faça pausas curtas a cada bloco e silencie notificações durante tarefas críticas.",
    "Crie um plano de melhoria para a categoria 'reuniao' com blocos menores e objetivos claros."
  ]
}
```

Novos atrativos do dashboard:
- `streak_dias`: maior sequência de dias consecutivos com registros no período.
- `faixas_de_ouro`: até 2 faixas horárias com maior média de foco no período.
- `comparativo_periodo_anterior`: delta de foco, tempo e sessões versus janela anterior de mesmo tamanho.

## Testes
```bash
pytest -q
```

Cobertura da suíte:
- criação válida
- validações de payload
- diagnóstico com base vazia
- cálculos de média e tempo total
- mensagem por faixa de foco
- agregação por categoria
- persistência real em SQLite
- dashboard com período default, validação de query e métricas analíticas
