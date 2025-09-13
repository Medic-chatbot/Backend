#!/usr/bin/env bash
set -euo pipefail

# Run Alembic migrations as a one-off ECS task using the API image/task definition.

REGION="${AWS_REGION:-ap-northeast-2}"
CLUSTER="${CLUSTER:-medic-gpu-cluster}"
API_FAMILY="${API_FAMILY:-medic-api-service}"
CONTAINER_NAME="${CONTAINER_NAME:-medic-api-container}"

echo "[migrate] Region=$REGION Cluster=$CLUSTER Family=$API_FAMILY Container=$CONTAINER_NAME"

echo "[migrate] Fetching latest API task definition ARN"
API_TD=$(aws ecs list-task-definitions \
  --family-prefix "$API_FAMILY" \
  --region "$REGION" \
  --sort DESC --no-paginate \
  --query 'taskDefinitionArns[0]' --output text)
echo "[migrate] TaskDefinition: $API_TD"

echo "[migrate] Reading service network configuration"
SUBNETS=$(aws ecs describe-services \
  --cluster "$CLUSTER" --services "$API_FAMILY" \
  --region "$REGION" \
  --query 'services[0].networkConfiguration.awsvpcConfiguration.subnets' \
  --output text)
SGS=$(aws ecs describe-services \
  --cluster "$CLUSTER" --services "$API_FAMILY" \
  --region "$REGION" \
  --query 'services[0].networkConfiguration.awsvpcConfiguration.securityGroups' \
  --output text)
ASSIGN_PUBLIC=$(aws ecs describe-services \
  --cluster "$CLUSTER" --services "$API_FAMILY" \
  --region "$REGION" \
  --query 'services[0].networkConfiguration.awsvpcConfiguration.assignPublicIp' \
  --output text)

if [[ -z "$SUBNETS" || "$SUBNETS" == "None" ]]; then
  echo "[migrate] ERROR: Could not determine service subnets. Ensure the service exists and has awsvpcConfiguration." >&2
  exit 1
fi

# Convert whitespace-separated to comma-separated
SUBNETS_CSV=$(echo "$SUBNETS" | tr '\t' ',' | tr ' ' ',')
SGS_CSV=$(echo "${SGS:-}" | tr '\t' ',' | tr ' ' ',')
if [[ -z "$SGS_CSV" ]]; then
  echo "[migrate] WARN: No security groups detected; proceeding without SG override"
fi

echo "[migrate] Running one-off Fargate task for Alembic upgrade"
OVERRIDES=$(cat << JSON
{
  "containerOverrides": [
    {
      "name": "${CONTAINER_NAME}",
      "command": ["bash", "-lc", "alembic upgrade head && alembic current"]
    }
  ]
}
JSON
)

ASSIGN_PUBLIC_LOWER=$(echo "${ASSIGN_PUBLIC:-DISABLED}" | tr '[:upper:]' '[:lower:]')
if [[ "$ASSIGN_PUBLIC_LOWER" != "enabled" ]]; then ASSIGN_PUBLIC_OPT=DISABLED; else ASSIGN_PUBLIC_OPT=ENABLED; fi

TASK_ARN=$(aws ecs run-task \
  --cluster "$CLUSTER" \
  --task-definition "$API_TD" \
  --launch-type FARGATE \
  --region "$REGION" \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS_CSV]$( [[ -n "$SGS_CSV" ]] && echo ",securityGroups=[$SGS_CSV]" ),assignPublicIp=$ASSIGN_PUBLIC_OPT}" \
  --overrides "$OVERRIDES" \
  --query 'tasks[0].taskArn' --output text)

if [[ -z "$TASK_ARN" || "$TASK_ARN" == "None" ]]; then
  echo "[migrate] ERROR: Failed to start migration task" >&2
  exit 1
fi

echo "[migrate] Started task: $TASK_ARN"

echo "[migrate] Waiting for task to stop..."
aws ecs wait tasks-stopped --cluster "$CLUSTER" --tasks "$TASK_ARN" --region "$REGION"

STATUS=$(aws ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK_ARN" --region "$REGION" --query 'tasks[0].containers[0].exitCode' --output text)
echo "[migrate] Task exit code: $STATUS"

if [[ "$STATUS" != "0" ]]; then
  echo "[migrate] ERROR: Alembic migration task failed with exit code $STATUS" >&2
  exit "$STATUS"
fi

echo "[migrate] Alembic migration completed successfully"
