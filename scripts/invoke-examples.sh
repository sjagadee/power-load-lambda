#!/usr/bin/env bash
# Usage: API_URL="https://<api-id>.execute-api.<region>.amazonaws.com/prod/DynamoDBManager" ./scripts/invoke-examples.sh
set -euo pipefail
: "${API_URL:?Set API_URL to your API Gateway POST endpoint}"
cd "$(dirname "$0")/../events"
for op in ping echo create read update list delete list; do
  echo "== $op"
  curl -s -X POST "$API_URL" -H "Content-Type: application/json" -d @"$op.json"
  echo
done
