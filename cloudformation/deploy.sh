#!/usr/bin/env bash
# Deploy the full stack.
# Usage: ./deploy.sh [stack-name] [region]  (extra Key=Value parameter overrides via PARAMS env)
#   e.g. PARAMS="LambdaMemorySize=1024 DeployPowerTuning=false" ./deploy.sh
set -euo pipefail
STACK="${1:-power-load-lambda}"
REGION="${2:-${AWS_REGION:-us-west-2}}"
cd "$(dirname "$0")"

aws cloudformation deploy \
  --region "$REGION" \
  --stack-name "$STACK" \
  --template-file template.yaml \
  --capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND \
  ${PARAMS:+--parameter-overrides $PARAMS}

aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK" \
  --query "Stacks[0].Outputs[].[OutputKey,OutputValue]" --output table
