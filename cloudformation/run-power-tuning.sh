#!/usr/bin/env bash
# Start a Power Tuning execution against the deployed function and print the visualization URL.
# Usage: ./run-power-tuning.sh [stack-name] [region]
set -euo pipefail
STACK="${1:-power-load-lambda}"
REGION="${2:-${AWS_REGION:-us-west-2}}"
cd "$(dirname "$0")"

out() { aws cloudformation describe-stacks --region "$REGION" --stack-name "$STACK" \
          --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text; }
SM_ARN=$(out PowerTuningStateMachineArn)
FN_ARN=$(out FunctionArn)
[ -n "$SM_ARN" ] && [ "$SM_ARN" != "None" ] || { echo "Power Tuning not deployed (DeployPowerTuning=false)"; exit 1; }

# Reuse the repo's input file, swapping in the real function ARN
INPUT=$(python3 -c "import json,sys; d=json.load(open('../power-tuning/state-machine-input.json')); d['lambdaARN']=sys.argv[1]; print(json.dumps(d))" "$FN_ARN")

EXEC_ARN=$(aws stepfunctions start-execution --region "$REGION" \
  --state-machine-arn "$SM_ARN" --input "$INPUT" --query executionArn --output text)
echo "Started: $EXEC_ARN"

while :; do
  STATUS=$(aws stepfunctions describe-execution --region "$REGION" --execution-arn "$EXEC_ARN" --query status --output text)
  [ "$STATUS" = "RUNNING" ] || break
  printf '.'; sleep 5
done
echo; echo "Status: $STATUS"
aws stepfunctions describe-execution --region "$REGION" --execution-arn "$EXEC_ARN" --query output --output text \
  | python3 -c "import json,sys; o=json.load(sys.stdin); print('Optimal memory:', o.get('power'), 'MB'); print('Visualization:', o.get('stateMachine',{}).get('visualization'))"
