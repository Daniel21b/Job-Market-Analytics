# AWS deployment contract

The production topology maps the local services to managed AWS components:

| Local component | AWS target | Responsibility |
|---|---|---|
| FastAPI container | ECS Fargate + Application Load Balancer | REST API and health endpoints |
| Worker container | ECS Fargate service | Redis queue consumer and EMR Serverless submitter |
| PostgreSQL | RDS PostgreSQL | Run metadata, normalized postings, skills, and relationships |
| Redis | ElastiCache for Redis | Cache-aside responses and processing queue |
| Local PySpark | EMR Serverless | Distributed normalization, deduplication, and skill extraction |
| Local data mounts | S3 raw/curated buckets | Immutable inputs, curated outputs, logs, and evidence |
| Environment file | Secrets Manager / task secrets | Database, Redis, and API configuration |

## Required production configuration

Set `EXECUTION_BACKEND=emr-serverless` on the worker and provide:

- `AWS_EMR_SERVERLESS_APPLICATION_ID`
- `AWS_EMR_SERVERLESS_EXECUTION_ROLE_ARN`
- `AWS_EMR_SERVERLESS_ENTRYPOINT_URI`
- `AWS_EMR_SERVERLESS_LOG_URI`
- `SKILL_TAXONOMY_PATH` as an S3 URI available to the EMR execution role

The ECS worker task role needs `emr-serverless:StartJobRun` and
`emr-serverless:GetJobRun` on the selected application. The EMR execution role needs read access to
the raw input and packaged application, write access to curated/log prefixes, and KMS permissions
when customer-managed encryption is enabled.

Use private subnets for RDS and ElastiCache, security-group ingress from ECS tasks only, TLS in
transit, encryption at rest, CloudWatch log groups with retention, and an AWS Budget alarm. Store no
long-lived AWS keys in the repository or container image.

## Evidence requirement

Every production run persists the ECS run identifier, EMR Serverless application/job-run IDs, S3
input/output URIs, partition profile, source row count, duplicate decisions, distinct canonical skill
count, and measured duration. Resume metrics are published only from these dated artifacts.
