# Free tier and security

roboto-guilliman is designed to stay inside GCP's free allowances where possible.
All infrastructure is Pulumi; all deploys run through GitHub Actions on push to `main`.

## Free tier budget

| Service | Free allowance (typical) | Our setting |
|---------|--------------------------|-------------|
| Cloud Run | 2M requests/mo, 180k vCPU-s, 360k GiB-s | `min-instances=0`, `max-instances=2`, `256Mi`, `cpu_idle=true` |
| Artifact Registry | 0.5 GB storage | Single service repo, tagged by git SHA |
| Firestore | Spark: 1 GiB, 50k reads / 20k writes per day | `(default)` database in Native mode, `europe-west1`; vector index uses native Firestore (no extra nodes) |
| Vertex AI (Gemini Flash-Lite) | Pay-per-token, very low cost | Cache hits skip the LLM entirely |
| Vertex AI (embeddings) | Ingest is one-off; queries are small | `text-embedding-004` at query time only |
| GitHub Actions | 2,000 min/mo (private repo) | Test + deploy ~5-8 min per push |

## What we deliberately avoid (not free)

- **Global HTTPS load balancer** - ~$18+/month minimum
- **Identity-Aware Proxy on a dedicated LB** - pairs with the above
- **VPC Service Controls** - enterprise perimeter product
- **Cloud Run min-instances > 0** - always-on billing
- **Cloud Build** - use GitHub Actions instead (already free tier eligible)

## Security without a paid load balancer

battleplan.uk already uses **Firebase Auth** (Google sign-in). The free-tier pattern:

1. Cloud Run allows unauthenticated **ingress** (no LB required).
2. The FastAPI service verifies a **Firebase ID token** on `POST /v1/ask` (next implementation step).
3. Only signed-in battleplan users get answers; everyone else receives `401`.

This gives you auth comparable to IAP for club use, at zero LB cost.

Optional hardening later: App Check, rate limiting via Firestore counters, or Cloud Armor if traffic grows.

## Single environment (no dev/stage)

roboto-guilliman uses **one GCP project** (`roboto-guilliman`) and **one Pulumi stack** (`main`). There is no separate dev, stage, or prod infrastructure.

**Why:**

- **Cost** - A second GCP project doubles WIF setup, secrets, billing alerts, and Artifact Registry overhead for little benefit on a scale-to-zero service.
- **Safety net** - Pull requests run ruff and pytest before merge; deploy only runs on push to `main`. Rollback is a git revert and redeploy (images tagged by git SHA).
- **Mission profile** - This is a club rules arbiter, not a payment or identity system. Brief downtime or a bad deploy is annoying, not catastrophic.

If traffic or stakes grow later (paid tiers, public SLA), add a staging project then - not before there is a concrete need.

All GCP resources use **`europe-west1`** (aligned with battleplan.uk).

## Pulumi stack (`infra/pulumi`)

Creates:

- Artifact Registry Docker repo
- Runtime service account + Firestore / Vertex IAM
- Firestore vector index on `warhammer_rules_11th.embedding`
- Cloud Run v2 service

Stack config lives in `Pulumi.main.yaml`. The container image URI is set by CI on each deploy.

## GitHub Actions secrets

| Secret | Purpose |
|--------|---------|
| `PULUMI_ACCESS_TOKEN` | Pulumi Cloud (free tier) state backend |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | WIF for keyless GCP auth from Actions |
| `GCP_SERVICE_ACCOUNT` | Deployer SA email - see deployer roles below |

**Simpler alternative:** replace the WIF auth step with `credentials_json: ${{ secrets.GCP_SA_KEY }}` if you have not set up Workload Identity Federation yet.

### Deployer service account roles (`github-actions-deploy`)

Required for CI `pulumi up` on the `main` stack:

| Role | Why |
|------|-----|
| `roles/run.admin` | Cloud Run service + IAM invoker binding |
| `roles/artifactregistry.admin` | Create Docker repo (writer is push-only) |
| `roles/datastore.user` | Runtime Firestore access |
| `roles/datastore.indexAdmin` | Firestore vector index |
| `roles/aiplatform.user` | Vertex AI (future runtime SA binding) |
| `roles/secretmanager.admin` | Secrets (Twilio keys later) |
| `roles/iam.serviceAccountUser` | Attach runtime SA to Cloud Run |
| `roles/iam.serviceAccountAdmin` | Create runtime service account |
| `roles/resourcemanager.projectIamAdmin` | Grant IAM to runtime SA |
| `roles/compute.viewer` | Pulumi GCP provider region lookup |

## Cost monitoring

Set a GCP billing budget alert at $1-5/month in the console. With min-instances=0 and query caching, idle cost should be near zero; spend tracks actual rules questions asked.
