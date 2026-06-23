# WhatsApp setup (whapi.cloud)

Get roboto-guilliman answering in your **existing** WhatsApp group with **`@roboto-guilliman`** mentions.

## What you need

1. A **dedicated SIM + phone** for the bot (PAYG is fine)
2. A [whapi.cloud](https://whapi.cloud) account (free Sandbox to start; $29-35/mo for production)
3. Cloud Run deployed with the WhatsApp env vars below

whapi.cloud links your WhatsApp account like WhatsApp Web. The bot joins your club group as a normal member and forwards group messages to Cloud Run.

## Setup checklist (once you have the SIM)

### 1. Create the whapi.cloud channel

1. Sign up at [panel.whapi.cloud](https://panel.whapi.cloud)
2. Create a channel and scan the QR code with WhatsApp on the bot phone
3. Copy the **API token** from the dashboard

### 2. Add the bot to your club group

On the bot phone, join your Warhammer club WhatsApp group like any other member.

### 3. Configure the webhook

In whapi.cloud channel settings, set:

- **Webhook URL:**
  ```
  https://roboto-guilliman-wifsng2koa-ew.a.run.app/webhook/whatsapp?secret=YOUR_SECRET
  ```
- **Events:** enable `messages` → `post`
- Click **Check webhook** (must return 200)

Generate a random `YOUR_SECRET` and store it as `WHAPI_WEBHOOK_SECRET` in Cloud Run.

### 4. Cloud Run env vars

| Variable | Value |
|----------|--------|
| `WHAPI_ENABLED` | `true` |
| `WHAPI_TOKEN` | From whapi.cloud dashboard |
| `WHAPI_WEBHOOK_SECRET` | Same secret as in webhook URL |
| `WHATSAPP_REQUIRE_MENTION` | `true` |
| `WHATSAPP_ALLOWED_GROUP_IDS` | Optional: club group ID once known |

To find your club group ID, send a test message in the group and check the whapi webhook payload - `chat_id` ends in `@g.us`. You can then lock the bot to that group only.

### 5. Test

In the club group:

```
@roboto-guilliman When does a unit take a Battle-shock test?
```

The bot should reply in the group thread within a few seconds.

## Behaviour

- **`@roboto-guilliman`** or **`@roboto`** triggers a rules lookup
- All other messages → ignored (no reply, no LLM call)
- Rate limit → 10 questions per sender per 60 seconds
- Legacy edition questions → in-character refusal (same as `/v1/ask`)

## Sandbox vs paid

| Plan | Cost | Good for |
|------|------|----------|
| Sandbox | Free | Integration testing (150 msgs/day) |
| Developer Premium | $29-35/mo | Club production use |

## Local testing

```powershell
# .env (or whatsapp-integration/.env.example vars in repo root .env)
WHAPI_ENABLED=true
WHAPI_TOKEN=your_token
WHAPI_WEBHOOK_SECRET=local-secret
```

Run the API and expose with [ngrok](https://ngrok.com/):

```
ngrok http 8080
```

Point whapi.cloud webhook at `https://<ngrok>/webhook/whatsapp?secret=local-secret`.

## Notes

- This uses WhatsApp Web (linked device), not Meta's official Business API. Keep message volume modest to avoid bans.
- The bot phone must stay online and WhatsApp session active.
- Replies are sent back to the same `chat_id` (group or DM).
