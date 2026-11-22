#!/usr/bin/env bash
# Delete everything the stack created (including the DynamoDB table and its data).
# Usage: ./destroy.sh [stack-name] [region]
set -euo pipefail
STACK="${1:-power-load-lambda}"
REGION="${2:-${AWS_REGION:-us-west-2}}"
read -r -p "Delete stack '$STACK' in $REGION, including all DynamoDB data? [y/N] " ok
[ "$ok" = "y" ] || { echo "Aborted"; exit 0; }
aws cloudformation delete-stack --region "$REGION" --stack-name "$STACK"
aws cloudformation wait stack-delete-complete --region "$REGION" --stack-name "$STACK"
echo "Stack deleted."
