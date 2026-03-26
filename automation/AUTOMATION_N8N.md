## Objetivo

Automatizar prospecção com base nos leads no MongoDB:

- Buscar leads com `email` válido e ainda não contatados
- Enviar e-mail de prospecção via SMTP (Gmail)
- Incluir link de WhatsApp (`wa.me`) quando houver `phone`
- Marcar o lead no Mongo com status de envio para evitar reenvio

## Pré-requisitos

- n8n rodando (cloud ou self-hosted)
- Acesso ao MongoDB Atlas/URI (mesmo que o seu app usa)
- Uma conta Gmail com **App Password** habilitada (SMTP)

## Campos (schema) usados no Mongo

Coleção: definida por `DB_NAME` e `COLLECTION_NAME` (no seu app é `linkedin_prospect.leads`).

O workflow vai ler e escrever estes campos:

- `email` (string)
- `phone` (string, opcional)
- `name` (string, opcional)
- `headline` (string, opcional)
- `linkedin_url` (string, chave)

Campos de automação (novos):

- `outreach_email_sent_at` (datetime): quando enviou
- `outreach_email_status` (string): `sent` | `error`
- `outreach_last_error` (string|null): detalhe do último erro
- `outreach_whatsapp_link` (string|null): link `wa.me` gerado (quando tiver phone)
- `outreach_disabled` (bool, opcional): se `true`, workflow ignora o lead

## Workflow n8n (import)

Importe o JSON:

- `automation/n8n/workflows/outreach_email_gmail_whatsapp_link.json`

No n8n:

- Menu `Workflows` → `Import from File`

## Configuração do node MongoDB

No node `MongoDB` (Find):

- **Database**: `linkedin_prospect` (ou o seu `DB_NAME`)
- **Collection**: `leads` (ou o seu `COLLECTION_NAME`)
- **Filter** (Mongo query):

```json
{
  "outreach_disabled": { "$ne": true },
  "outreach_email_sent_at": { "$exists": false },
  "email": { "$type": "string", "$ne": "" }
}
```

> Observação: seu app já valida e só salva leads com email válido (filtro no pipeline). Mesmo assim o filtro acima protege.

## Configuração do SMTP (Gmail)

No node `SMTP`:

- **Host**: `smtp.gmail.com`
- **Port**: `587`
- **Secure**: `false` (STARTTLS)
- **User**: seu e-mail Gmail
- **Password**: App Password do Gmail

Limites: Gmail tem limites diários de envio. Comece com `BATCH_SIZE=10` e aumente com cuidado.

## Template (personalização)

O template fica dentro do node `Code` no workflow. Você pode ajustar:

- assunto
- corpo (texto)
- texto do WhatsApp

## Execução segura (primeiro teste)

1. No node `Code`, deixe `BATCH_SIZE=1`
2. Rode manualmente uma execução
3. Verifique no Mongo se `outreach_email_sent_at` foi setado
4. Só então ative o workflow e aumente batch

