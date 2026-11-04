# ADR: Deployment & Operations (Platform, HA, Deploys, Observability, Security)

## Status

Accepted. 2026-10-09.

## Context

App currently runs as a single Railway deployment (Dockerized Django +
React + nginx gateway, no redundancy). Migrating to a cloud platform with
real HA, self-managed by the team for cost control and operational
learning, not handed to a PaaS.

Evaluated: Azure (team has work familiarity), GCP (team 1 used it with
GKE), DigitalOcean. Budget source: GitHub Student Developer Pack credits,
one-semester timeline.

DigitalOcean was the initial pick (cheapest, longest credit, simplest
primitives for Ansible). Reversed: DigitalOcean left the Student Developer
Pack. All pack credits, including already-redeemed ones, expired 2026-08-01.
No DigitalOcean student credit currently exists.

A second revision: compute was first planned as 2 self-managed VMs +
Ansible. Reversed again: team decided to run on AKS instead, trading the
Ansible-built rolling-update/rollback pipeline for k8s-native deploy
mechanics, matching team 1's GKE pattern. Both reversals are captured here
rather than in separate ADRs, since the platform (Azure) and most
supporting decisions (DB, observability, security) carried through
unchanged.

## Decision

### Platform: Microsoft Azure

Azure for Students stacks three benefits:

1. $100 credit, 12 months, renewable annually while verified as a student.
2. Monthly free amounts of 20+ services, 12 months from signup, not drawn
   from the credit. Covers nearly this entire architecture at $0/mo for the
   first year (see cost table).
3. 65+ "always free" services, no expiration, not tied to student status.
   AKS's control plane is in this tier: free on every Azure account,
   permanently, independent of the 12-month window.

GCP's $300 credit is larger but is a 90-day trial, hard expiry regardless
of spend rate. DigitalOcean has no student offer. Azure's 12-month free
tier plus AKS's permanently-free control plane covers the full semester
and beyond.

### Compute: AKS, 2 node pools, mixed architecture

AKS control plane: Free tier, $0/cluster/hr, no SLA (confirmed always-free
on the account dashboard, not a 12-month allocation). No SLA is acceptable
for a class project; matches team 1's non-SLA-tier GKE choice.

Node pools use the same free VM allocation as the earlier VM-only plan:

| Node pool | Free allocation | Architecture |
|---|---|---|
| Pool 1 (system + app) | 750 hrs/mo, B2ats v2, 2 vCPU / 1 GiB | AMD64 |
| Pool 2 (app) | 750 hrs/mo, B2pts v2, 2 vCPU / 1 GiB | ARM64 |

**Use classic AKS with manually-specified node pools, not "AKS Automatic."**
Automatic mode selects its own VM sizes and would bypass the free-tier SKUs
entirely. Manual node pools let the VM size be pinned to B2ats_v2/B2pts_v2
directly in Terraform.

**Constraint carried over from the VM plan: the two node pools are
different CPU architectures.** AKS schedules by the built-in
`kubernetes.io/arch` node label, so this is a native fit, better than the
hand-rolled Ansible `arch` inventory variable from the earlier plan, but
still a standing constraint:

- Docker images built multi-arch (`docker buildx build --platform
  linux/amd64,linux/arm64`), pushed to Azure Container Registry as a
  manifest list.
- Deployment manifests use `nodeAffinity`/`nodeSelector` on
  `kubernetes.io/arch` to place pods correctly; a Deployment with 2 replicas
  and no affinity rule can schedule both replicas on the same architecture,
  defeating the redundancy.
- Native/C-extension dependencies (psycopg, etc.) verified for ARM64
  wheels in CI, not assumed.

Post-free-year standalone node pricing unchanged from the VM plan: B2ats v2
~$6.86/mo, B2pts v2 ~$6.13/mo. AKS control plane remains $0/cluster/hr
regardless.

### Image registry: Azure Container Registry

ACR, Standard tier, free for 12 months (100GB storage, 10 webhooks).
Replaces Docker Hub; holds the multi-arch manifest list.

### High availability: app tier only, DB is the accepted ceiling

Unchanged reasoning from the VM-based plan, restated for k8s primitives:

- **App tier:** Deployment with 2 replicas, one per architecture/node pool
  (via nodeAffinity), `PodDisruptionBudget` ensuring at least 1 replica
  stays up during voluntary disruption, behind the AKS-provisioned Azure
  Load Balancer (Standard SKU, created automatically by a `LoadBalancer`-
  type Service). Survives a single node or pod failure. Required for
  zero-downtime rolling deploys, same constraint as before, just enforced
  by the k8s Deployment controller instead of an Ansible `serial: 1` loop.
- **Database:** Postgres Flexible Server, Burstable B1MS, single node, no
  zone-redundant standby, kept outside the cluster as a managed service.
  Zone-redundant HA roughly doubles DB compute cost; not justified on this
  budget. Team 1 made the same call on GCP (zonal, not regional, Cloud
  SQL).
- **Reasoning:** system availability is `P(db) x P(app)`, not `min()`. DB
  single-node sets the availability ceiling. App-tier redundancy still
  matters: marginal cost is $0 for year one, and app-tier failures
  (crashes, bad deploys, node drains) are independent of, and more
  frequent than, managed-DB failures. Dropping app HA does not avoid cost
  already paid by the DB ceiling; it adds a second, more frequent failure
  mode on top of it.
- Upgrade path: zone-redundant HA before a specific high-stakes window
  (demo day, final grading), if budget allows.

### Provisioning: Terraform, not Ansible, for cloud resources

Terraform (azurerm provider): state-tracked, declarative. `plan` shows a
diff before any change; drift between declared and live state is caught
automatically.

**Split:** Terraform provisions the AKS cluster and both node pools, ACR,
Load Balancer (via the cluster's Service resources), Postgres Flexible
Server, Storage Account (Blob container for media), Key Vault, Virtual
Network, and Network Security Groups. Kubernetes manifests (kustomize,
matching team 1's structure) configure what runs in the cluster: Deployment,
Service, PodDisruptionBudget, SecretProviderClass, migration Job. No
Ansible role in this plan; the in-droplet configuration work Ansible would
have done is replaced by k8s-native primitives.

### Deploy and rollback: k8s-native rolling update

- Migrations run as a separate k8s Job, gated before the Deployment
  rollout proceeds, same pattern as team 1's GKE pipeline.
- Deployment `strategy.rollingUpdate` with `maxUnavailable: 0` rolls pods
  one at a time, health-checked via readiness probe before the next pod is
  taken down.
- Rollback: `kubectl rollout undo` to the previous ReplicaSet on a failed
  rollout or failed smoke test. Automating this (team 1 built a bash
  script around `kubectl rollout status` + smoke test + `rollout undo`) is
  a task for the CI/CD plan, not this ADR.
- GitHub Actions on push to `main`: test/lint gate, build and push the
  multi-arch image to ACR, apply the migration Job, apply the Deployment,
  wait on rollout status, smoke test, roll back on failure, post result to
  Discord/Slack webhook.

### Observability: Grafana Cloud (free tier), Sentry, Honeybadger

Platform-agnostic, unchanged:

| Tool | Role | Cost |
|---|---|---|
| Grafana Cloud | Cluster/pod/Postgres metrics (via Grafana Alloy or kube-state-metrics), logs, alerting | $0 (free tier: 10k series, 50GB logs/mo) |
| Sentry (student pack) | App exceptions, React frontend error capture | $0 (50K errors/mo, 1yr renewable) |
| Honeybadger (student pack) | Cron heartbeat, hourly alert-matching job (runs as a k8s CronJob) | $0 |

Datadog (student pack, 2yr free) rejected: free access tied to student
status. Grafana Cloud's free tier is not.

### Security: right-sized, not SIEM

SIEM correlates events across large fleets. A 2-node cluster and 1 managed
DB is not a fleet. Mapped to Azure/AKS primitives:

| Concern | Tool | Cost |
|---|---|---|
| SSH access control | 1Password Dev Tools (student pack): key-only auth, signed commits. Reduced scope vs the VM plan: AKS nodes aren't SSH'd into directly, this now covers CI/registry/Terraform access, not node shell access | $0 (1yr) |
| Secrets management | Key Vault Provider for Secrets Store CSI Driver (AKS add-on, free: 10,000 transactions/mo, 12 months), mounting secrets into pods, same pattern as team 1's Secret Manager CSI. Doppler (student pack) remains an option for CI-side secrets | $0 |
| Dependency/secret scanning | Snyk (student pack) or GitHub Dependabot + secret scanning | $0 |
| Network exposure | AKS Network Policy + Azure NSGs: inbound limited to the Load Balancer (80/443); no direct node SSH exposure by default | $0 (built-in) |
| Audit trail | Azure Activity Log + AKS audit logs | $0 (built-in) |
| Anomaly detection | Grafana Cloud alerting (pod restarts, error-rate, resource pressure) | $0 (already budgeted) |

### Total cost

**First 12 months**, using free allocations above:

| Component | Cost/mo |
|---|---|
| AKS control plane, Free tier | $0 |
| 2x node (B2ats v2 + B2pts v2) | $0 |
| Load Balancer, Standard (via AKS Service) | $0 |
| Azure Container Registry, Standard | $0 |
| Postgres Flexible Server, Burstable B1MS | $0 |
| Managed Disks (node OS disks) | $0 |
| Blob Storage (media, under 5GB) | $0 |
| Key Vault | $0 |
| Bandwidth (under 15GB outbound) | $0 |
| Monitoring / security tooling | $0 |
| **Total** | **$0/mo** |

$100 credit unused by this budget, serves as overflow buffer for anything
exceeding a free allocation.

**After the 12-month window** (pay-as-you-go, no free allocations):

| Component | Cost/mo |
|---|---|
| AKS control plane, Free tier | $0 (always-free, not time-limited) |
| 2x node | ~$13 |
| Load Balancer, Standard | ~$16.43 |
| Azure Container Registry, Standard | ~$20 |
| Postgres Flexible Server, Burstable B1MS | ~$12 |
| Blob Storage | ~$1 |
| **Total** | **~$62/mo** |

Higher than the VM-only plan's post-free-year estimate (~$42/mo), the
difference is ACR's standalone cost (~$20/mo once its own 12-month free
allocation ends). Out of scope either way: the semester ends before the
free window does.

## Consequences

- Team trades the Ansible-built deploy/rollback pipeline for k8s-native
  rollout mechanics. Less custom code to maintain, but the thing being
  learned shifts from "build a deploy pipeline" to "operate a k8s
  cluster," a deliberate choice, not a smaller one.
- Node pools are different CPU architectures (AMD64, ARM64). Every build,
  dependency check, and Deployment affinity rule accounts for this as a
  standing pipeline constraint, not a one-time setup cost.
- DB is a documented single point of failure, kept outside the cluster.
  A DB outage takes the app down regardless of pod-level redundancy.
  Accepted for this budget; documented here so it is not mistaken for an
  oversight later.
- Observability/security tooling tied to the student pack (Sentry,
  Honeybadger, 1Password, Doppler, Snyk) needs a migration plan if the
  project outlives student status. Grafana Cloud, GitHub's native
  Dependabot/secret scanning, Azure Key Vault's always-free tier, and
  AKS's always-free control plane do not have this dependency.
- Revisit if: traffic threatens the 1 GiB node headroom, the project needs
  to outlive the course (the 12-month allocations on ACR/Postgres/LB do
  not, AKS's control plane and Key Vault's always-free tier do), or budget
  allows DB zone-redundant HA before a high-stakes demo.
