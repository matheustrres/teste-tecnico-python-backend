# 🚀 Desafio Técnico: API de Foco e Produtividade

O objetivo deste teste é criar o backend de um **"Log de Performance"**. Em vez de apenas registrar tarefas, queremos entender o **estado de fluxo** do desenvolvedor ou estudante durante suas atividades.

## ✅ Implementação deste fork
- Documentação da solução implementada: `API.md`
- Stack usada: Python + FastAPI + SQLite
- Endpoints extras de valor ao usuário final:
  - `GET /dashboard-produtividade` (score de consistência, alerta de queda de foco, recomendações por categoria)
  - Timezone do dashboard configurável por `DASHBOARD_TIMEZONE` (ver `.env.example`)

## 🔎 Checklist de Entrega
- [ ] Criar e ativar ambiente virtual
- [ ] Instalar dependências: `pip install -r requirements.txt`
- [ ] Executar testes: `pytest -q`
- [ ] Subir API: `uvicorn app.main:app --reload`
- [ ] Validar rotas em `http://127.0.0.1:8000/docs`

## 📅 Regras de Entrega

* Prazo: O projeto deve ser entregue até a próxima segunda-feira.
* Uso de IA: O uso de ferramentas de Inteligência Artificial (ChatGPT, GitHub Copilot, etc.) é permitido.
* Transparência: Caso utilize IA, você deve commitar os artefatos gerados junto ao repositório. Queremos entender como você utiliza essas ferramentas para acelerar seu fluxo de trabalho.
* Faça o **fork desse projeto** e me avise quando terminar o [wouerner](https://www.linkedin.com/in/wouerner/) no linkedin. (necessario para pode acompanhar pelo github quem participou)

## 📝 O Contexto
Muitas vezes trabalhamos muito, mas produzimos pouco. Você deve construir uma API simples que ajude o usuário a registrar seu nível de produtividade e, ao final, entregue um **diagnóstico inteligente** de como foi o seu período de trabalho.

## 🛠 Requisitos Técnicos
*   **Linguagem:** Python 3.x.
*   **Framework:** À sua escolha (FastAPI, Flask, Django, etc).
*   **Armazenamento:** Pode ser em memória (dicionários/listas) ou SQLite para simplicidade.
*   **Diferencial:** Código limpo, bem comentado e presença de um `README.md` explicando como rodar o projeto.

---

## 🛣 Os Endpoints

### 1. `POST /registro-foco`
O usuário deve enviar os dados de um bloco de trabalho recém-encerrado.

**Campos obrigatórios:**
*   `nivel_foco`: Um valor inteiro de **1 a 5** (onde 1 é "muito distraído" e 5 é "estado de flow").
*   `tempo_minutos`: Um inteiro representando quanto tempo durou a sessão.
*   `comentario`: Uma string descrevendo o que foi feito ou o que causou distração.

> **💡 Dica de Criatividade:** Sinta-se à vontade para adicionar campos extras, como `categoria` (coding, reunião, estudo), `data` ou `tags`.

### 2. `GET /diagnostico-produtividade`
Este endpoint deve retornar um resumo inteligente baseado em todos os registros salvos.

**O que deve retornar (JSON):**
*   **Média do nível de foco:** A média aritmética de todos os registros.
*   **Tempo total focado:** A soma de todos os minutos registrados.
*   **Lógica Criativa (Diferencial):** Uma "mensagem de feedback" automática baseada nos dados analisados.
    *   *Exemplo:* Se a média de foco for `< 3`, sugerir "Pausas mais longas e menos notificações". Se for `> 4`, "Você está em uma maratona produtiva de alto nível!".

---

## 📊 O que será avaliado
1.  **Organização do Código:** Estrutura de pastas e legibilidade.
2.  **Manipulação de Dados:** Como você lida com tipos, cálculos e persistência.
3.  **Tratamento de Erros:** Respostas adequadas para entradas inválidas (ex: nível de foco fora do range 1-5).
4.  **Criatividade:** Pequenos detalhes que tornam a API mais útil para o usuário final.
