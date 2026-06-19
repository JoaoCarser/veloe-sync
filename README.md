# VELOE-SYNC

Pipeline automatizado para sincronizar os **abastecimentos Veloe/Alelo** com o Monday.com, mantendo o board sempre atualizado com os registros do semestre vigente.

---

## O que ele faz

- Autentica na API Veloe/Alelo e busca todos os veículos ativos
- Calcula o período do semestre vigente (Jan–Jun ou Jul–Dez)
- Busca os IDs técnicos de todos os abastecimentos do semestre por janelas de 7 dias
- Compara os registros Veloe com os itens já existentes no Monday
- Busca dados completos apenas dos abastecimentos novos (não cadastrados)
- Cria os itens faltantes no Monday com todos os 37 campos mapeados
- Detecta e remove duplicados (mantém o menor `id_monday`)
- Detecta e remove órfãos (itens no Monday sem correspondência na Veloe)
- Envia resumo operacional ao webhook n8n ao final de cada execução

---

## Estrutura

```
veloe-sync/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── src/
    ├── main.py
    ├── config/
    │   └── settings.py
    ├── shared/
    │   ├── logger.py
    │   ├── normalize_text.py
    │   ├── retry.py
    │   └── chunks.py
    ├── veloe/
    │   ├── api_client.py
    │   ├── login.py
    │   ├── date_periods.py
    │   ├── build_supply_id.py
    │   ├── map_supply_data.py
    │   ├── fetch_vehicles.py
    │   ├── fetch_supplies.py
    │   └── fetch_full_supplies.py
    ├── monday/
    │   ├── api_client.py
    │   ├── fetch_item_names.py
    │   ├── fetch_full_items.py
    │   ├── build_item_payload.py
    │   ├── create_items.py
    │   └── delete_items.py
    ├── sync/
    │   ├── compare_records.py
    │   ├── find_duplicates.py
    │   ├── find_orphans.py
    │   └── run_cleanup.py
    ├── summary/
    │   └── build_summary.py
    └── webhook/
        └── send_to_n8n.py
```

---

## Configuração

Copie `.env.example` para `.env` e preencha as variáveis:

```env
# Veloe / Alelo
VELOE_API_BASE_URL=
VELOE_CLIENT_ID=
VELOE_CLIENT_SECRET=
VELOE_CONTRACT=

# Monday
MONDAY_API_TOKEN=
MONDAY_API_URL=https://api.monday.com/v2
MONDAY_BOARD_ID=
MONDAY_BOARD_NAME=

# n8n
N8N_SUMMARY_WEBHOOK_URL=
```

Variáveis operacionais (opcionais):

```env
MONDAY_PAGE_SIZE=500
HTTP_MAX_RETRIES=5
HTTP_REQUEST_TIMEOUT=60
VELOE_SUPPLY_BATCH_SIZE=100
VELOE_SUPPLY_WINDOW_DAYS=7
PIPELINE_SHOW_PROGRESS=true
```

Dry-runs por ação (default: `false` — executa de verdade):

```env
PIPELINE_CREATE_DRY_RUN=false
PIPELINE_DELETE_DUPLICATE_DRY_RUN=false
PIPELINE_DELETE_ORPHAN_DRY_RUN=false
```

---

## Execução

### Local
```bash
python -u -m src.main
```

### Docker
```bash
docker compose up --build
```

---

## Etapas do pipeline

| # | Etapa | Descrição |
|---|-------|-----------|
| 01 | Validar ambiente | Checa variáveis obrigatórias |
| 02 | Autenticar na Veloe | Login com clientId/clientSecret |
| 03 | Buscar veículos | Paginação por placa |
| 04 | Calcular período | Semestre vigente com fallback para ontem |
| 05 | Buscar IDs Veloe | Supply IDs por janelas de 7 dias |
| 06 | Buscar registros Monday | Nomes atuais do board para comparação |
| 07 | Comparar Veloe × Monday | Identifica abastecimentos não cadastrados |
| 08 | Buscar dados completos | 37 campos dos registros novos |
| 09 | Montar payloads | Mapeia campos Veloe → colunas Monday |
| 10 | Criar itens | Cria apenas os faltantes no Monday |
| 11 | Limpeza | Remove duplicados e órfãos |
| 12 | Resumo final | Consolida contadores de todas as etapas |
| 13 | Webhook n8n | Envia resumo ao endpoint configurado |

---

## Regras de negócio

- **ID técnico do abastecimento:** `{placa} - {authorization} - {data_iso}` — chave única que evita duplicidade entre Veloe e Monday.
- **Janela de datas:** consultas em blocos de 7 dias para contornar limites da API Veloe.
- **Duplicados:** mantém o item com menor `id_monday` (numérico) e apaga os demais.
- **Órfãos:** item no Monday cujo ID técnico não existe nos abastecimentos Veloe do semestre.
- **Fallback de data:** se a API retornar HTTP 400 para o fim do semestre, reusa a data de ontem como `endDate`.

---

## Segurança

- Credenciais exclusivamente via `.env` (não versionar)
- Execução conteinerizada
- Retry/backoff com jitter para todas as chamadas REST e GraphQL
- Dry-run por tipo de ação para operações destrutivas

---

## 🤝 Autor

**João Carser**  
[github.com/JoaoCarser](https://github.com/JoaoCarser)

