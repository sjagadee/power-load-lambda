# CloudFormation: one-command setup

`template.yaml` builds everything from the [step-by-step guide](../docs/step-by-step-guide.md) as a single stack.

| Resource | Type | Default name / setting |
|---|---|---|
| DynamoDB table | `AWS::DynamoDB::Table` | `lambda-apigateway`, PK `id` (S), on-demand |
| CloudWatch log group | `AWS::Logs::LogGroup` | `/aws/lambda/LambdaFunctionOverHttps`, 14-day retention |
| DynamoDB CRUD policy | `AWS::IAM::ManagedPolicy` | Scoped to the table ARN |
| CloudWatch Logs policy | `AWS::IAM::ManagedPolicy` | Scoped to the function's log group |
| Lambda execution role | `AWS::IAM::Role` | Both policies attached |
| Lambda function | `AWS::Lambda::Function` | `LambdaFunctionOverHttps`, Python 3.12, **512 MB**, 5 s |
| REST API | `AWS::ApiGateway::RestApi` | `DynamoDBOperations`, Regional |
| Resource + method | `AWS::ApiGateway::Resource` / `Method` | `POST /DynamoDBManager`, Lambda (non-proxy) integration |
| Invoke permission | `AWS::Lambda::Permission` | Only this API's `POST /DynamoDBManager` can invoke |
| Deployment + stage | `AWS::ApiGateway::Deployment` / `Stage` | `prod`, throttled to 100 req/s (burst 200) |
| Power Tuning *(optional)* | `AWS::Serverless::Application` | SAR `aws-lambda-power-tuning`, restricted to this function |

## Prerequisites

- AWS CLI v2, configured with `aws configure`, with permission to create the resources above
- Python 3, used by `run-power-tuning.sh`

## Deploy

```bash
cd cloudformation
./deploy.sh                          # stack "power-load-lambda" in us-west-2
./deploy.sh my-stack us-east-1       # custom stack name / region
PARAMS="LambdaMemorySize=1024 DeployPowerTuning=false" ./deploy.sh
```

The script prints the stack outputs when it finishes:

| Output | Use it for |
|---|---|
| `ApiUrl` | Postman's `api_url` variable, or `API_URL` for `scripts/invoke-examples.sh` |
| `FunctionArn` | `lambdaARN` in the Power Tuning input |
| `PowerTuningStateMachineArn` | Starting a tuning run |

> **Already built it by hand?** The default names (`LambdaFunctionOverHttps`, `lambda-apigateway`) must be unique in the Region. Either delete the manual resources first or override the names: `PARAMS="FunctionName=crud-cfn TableName=crud-cfn"`.

## Run Power Tuning

```bash
./run-power-tuning.sh
```

This reads [`../power-tuning/state-machine-input.json`](../power-tuning/state-machine-input.json), fills in the real function ARN, starts an execution, waits for it to finish, and prints the optimal memory and the visualization link.

## Load test

Import [`../postman/00_load_test_v22.postman_collection.json`](../postman/00_load_test_v22.postman_collection.json), set `api_url` to the `ApiUrl` output, and follow section 8 of the guide. To compare memory sizes, redeploy with a different `LambdaMemorySize`:

```bash
PARAMS="LambdaMemorySize=128" ./deploy.sh    # baseline
PARAMS="LambdaMemorySize=512" ./deploy.sh    # balanced
```

The stage throttle (100 req/s) is well above the ~49 req/s reached in testing. Raise `ThrottlingRateLimit` if you test with more virtual users.

## Parameters

| Parameter | Default | Notes |
|---|---|---|
| `FunctionName` | `LambdaFunctionOverHttps` | |
| `TableName` | `lambda-apigateway` | |
| `ApiName` | `DynamoDBOperations` | |
| `StageName` | `prod` | Becomes part of the URL |
| `LambdaMemorySize` | `512` | 128–2048 |
| `LambdaTimeout` | `5` | Seconds, max 29 (API Gateway's limit) |
| `LogRetentionDays` | `14` | |
| `ThrottlingRateLimit` / `ThrottlingBurstLimit` | `100` / `200` | Protects the open endpoint from abuse and runaway cost |
| `DeployPowerTuning` | `true` | Set to `false` to skip the state machine |
| `PowerTuningVersion` | `4.3.6` | SAR app version |

## Tear down

```bash
./destroy.sh
```

This deletes the whole stack, including the nested Power Tuning stack and the DynamoDB table **and its data**.

## Notes

- The Lambda code is inlined in the template (`ZipFile`), so no S3 bucket is needed. After editing `lambda/lambda_function.py`, regenerate the template with `python3 scripts/generate_cfn.py .` from the repo root.
- `CAPABILITY_AUTO_EXPAND` is required because the template uses the SAM transform to pull in the Power Tuning app. `CAPABILITY_IAM` is required because it creates IAM roles and policies.
- The API has no authentication, as in the original lab. For anything beyond a demo, add an API key with a usage plan, IAM auth or a Cognito authorizer.
