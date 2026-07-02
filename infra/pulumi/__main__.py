"""Pulumi stack: free-tier Cloud Run + IAM + Firestore vector index."""

from __future__ import annotations

import pulumi
import pulumi_gcp as gcp

config = pulumi.Config()
project = gcp.config.project
region = gcp.config.region

service_name = config.get("serviceName")
firestore_collection = config.get("firestoreCollection")
image = config.require("image")
max_instances = int(config.get("maxInstances"))
memory = config.get("memory")

labels = {
    "managed-by": "pulumi",
    "service": service_name,
}

# Artifact Registry (0.5 GB/month free). Images are pushed by GitHub Actions.
artifact_repo = gcp.artifactregistry.Repository(
    "docker_repo",
    repository_id=service_name,
    location=region,
    format="DOCKER",
    description="roboto-guilliman container images",
    labels=labels,
)

runtime_sa = gcp.serviceaccount.Account(
    "runtime",
    account_id=service_name,
    display_name="roboto-guilliman Cloud Run runtime",
)

gcp.projects.IAMMember(
    "runtime_firestore",
    project=project,
    role="roles/datastore.user",
    member=runtime_sa.email.apply(lambda email: f"serviceAccount:{email}"),
)

gcp.projects.IAMMember(
    "runtime_vertex",
    project=project,
    role="roles/aiplatform.user",
    member=runtime_sa.email.apply(lambda email: f"serviceAccount:{email}"),
)

# One-time vector index for nearest-neighbor search (768-dim text-embedding-004).
vector_index = gcp.firestore.Index(
    "rules_vector_index",
    project=project,
    collection=firestore_collection,
    query_scope="COLLECTION",
    fields=[
        gcp.firestore.IndexFieldArgs(
            field_path="__name__",
            order="ASCENDING",
        ),
        gcp.firestore.IndexFieldArgs(
            field_path="embedding",
            vector_config=gcp.firestore.IndexFieldVectorConfigArgs(
                dimension=768,
                flat=gcp.firestore.IndexFieldVectorConfigFlatArgs(),
            ),
        ),
    ],
)

cloud_run = gcp.cloudrunv2.Service(
    "api",
    name=service_name,
    location=region,
    ingress="INGRESS_TRAFFIC_ALL",
    deletion_protection=False,
    labels=labels,
    template=gcp.cloudrunv2.ServiceTemplateArgs(
        service_account=runtime_sa.email,
        scaling=gcp.cloudrunv2.ServiceTemplateScalingArgs(
            min_instance_count=0,
            max_instance_count=max_instances,
        ),
        containers=[
            gcp.cloudrunv2.ServiceTemplateContainerArgs(
                image=image,
                ports=gcp.cloudrunv2.ServiceTemplateContainerPortsArgs(container_port=8080),
                resources=gcp.cloudrunv2.ServiceTemplateContainerResourcesArgs(
                    limits={
                        "cpu": "1",
                        "memory": memory,
                    },
                    cpu_idle=True,
                    startup_cpu_boost=False,
                ),
                envs=[
                    gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                        name="GCP_PROJECT_ID",
                        value=project,
                    ),
                    gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                        name="GCP_LOCATION",
                        value=region,
                    ),
                    gcp.cloudrunv2.ServiceTemplateContainerEnvArgs(
                        name="FIRESTORE_COLLECTION",
                        value=firestore_collection,
                    ),
                ],
            ),
        ],
    ),
    opts=pulumi.ResourceOptions(
        depends_on=[vector_index],
        # CI deploys container images with gcloud; Pulumi owns service shell + env.
        ignore_changes=["template.containers[0].image"],
        custom_timeouts=pulumi.CustomTimeouts(update="10m"),
    ),
)

# Public Cloud Run URL; lock down at the app layer with Firebase ID tokens (see docs).
public_invoker = gcp.cloudrunv2.ServiceIamMember(
    "public_invoker",
    name=cloud_run.name,
    location=region,
    role="roles/run.invoker",
    member="allUsers",
)

pulumi.export("artifact_registry", artifact_repo.name)
pulumi.export("cloud_run_uri", cloud_run.uri)
pulumi.export("runtime_service_account", runtime_sa.email)
pulumi.export("vector_index_name", vector_index.name)
