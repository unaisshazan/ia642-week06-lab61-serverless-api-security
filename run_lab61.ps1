# IA 642 Lab 6.1 - robust Windows runner (JSON via files)
$ErrorActionPreference = "Continue"
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
$env:AWS_DEFAULT_REGION = "us-east-1"
$env:AWS_REGION = "us-east-1"

$ROOT = Split-Path -Parent $MyInvocation.MyCommand.Path
$CODE = Join-Path $ROOT "code"
$EV = Join-Path $ROOT "evidence"
$TMP = Join-Path $ROOT "tmp"
New-Item -ItemType Directory -Force -Path $EV,$TMP | Out-Null
Set-Location $ROOT
$PREFIX = "ia642-lab"

function Save-Ev([string]$name, [string]$content) {
  $path = Join-Path $EV $name
  Set-Content -Path $path -Value $content -Encoding utf8
  Write-Host "=== $name ==="
  Write-Host $content
}

function AwsOk([string]$msg) {
  if ($LASTEXITCODE -ne 0) { Write-Host "WARN: $msg exit=$LASTEXITCODE" }
}

# --- teardown leftovers ---
Write-Host "Cleaning leftovers..."
$oldApis = aws apigatewayv2 get-apis --query "Items[?Name=='$PREFIX-api'].ApiId" --output text 2>$null
if ($oldApis) { foreach ($a in ($oldApis -split '\s+')) { if ($a) { aws apigatewayv2 delete-api --api-id $a 2>$null | Out-Null } } }
aws lambda delete-function --function-name "$PREFIX-api" 2>$null | Out-Null
aws dynamodb delete-table --table-name "$PREFIX-accounts" 2>$null | Out-Null
$pools = aws cognito-idp list-user-pools --max-results 20 --query "UserPools[?Name=='$PREFIX-pool'].Id" --output text 2>$null
if ($pools) { foreach ($p in ($pools -split '\s+')) { if ($p) { aws cognito-idp delete-user-pool --user-pool-id $p 2>$null | Out-Null } } }
aws iam delete-role-policy --role-name "$PREFIX-role" --policy-name app 2>$null | Out-Null
aws iam delete-role --role-name "$PREFIX-role" 2>$null | Out-Null
Start-Sleep -Seconds 8

$id = aws sts get-caller-identity --output json | ConvertFrom-Json
$ACCT = $id.Account
Save-Ev "00_identity.json" ($id | ConvertTo-Json -Depth 5)

# trust + policy files
Set-Content -Encoding ascii (Join-Path $TMP "trust.json") '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
Set-Content -Encoding ascii (Join-Path $TMP "policy.json") '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Action":["dynamodb:GetItem","dynamodb:PutItem","dynamodb:Query","dynamodb:UpdateItem"],"Resource":"*"},{"Effect":"Allow","Action":["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],"Resource":"*"}]}'

$ROLE_ARN = aws iam create-role --role-name "$PREFIX-role" --assume-role-policy-document "file://tmp/trust.json" --query "Role.Arn" --output text
AwsOk "create-role"
if (-not $ROLE_ARN -or $ROLE_ARN -eq "None") { $ROLE_ARN = "arn:aws:iam::${ACCT}:role/$PREFIX-role" }
aws iam put-role-policy --role-name "$PREFIX-role" --policy-name app --policy-document "file://tmp/policy.json"
AwsOk "put-role-policy"
Save-Ev "01_role_arn.txt" $ROLE_ARN
Start-Sleep -Seconds 12

aws dynamodb create-table --table-name "$PREFIX-accounts" --attribute-definitions AttributeName=account_id,AttributeType=S --key-schema AttributeName=account_id,KeyType=HASH --billing-mode PAY_PER_REQUEST --query "TableDescription.TableStatus" --output text
AwsOk "create-table"
aws dynamodb wait table-exists --table-name "$PREFIX-accounts"

Set-Content -Encoding ascii (Join-Path $TMP "item1001.json") '{"account_id":{"S":"1001"},"owner":{"S":"alice"},"balance":{"N":"4200"},"card_last4":{"S":"4242"}}'
Set-Content -Encoding ascii (Join-Path $TMP "item1002.json") '{"account_id":{"S":"1002"},"owner":{"S":"bob"},"balance":{"N":"98750"},"card_last4":{"S":"7733"}}'
aws dynamodb put-item --table-name "$PREFIX-accounts" --item "file://tmp/item1001.json"
aws dynamodb put-item --table-name "$PREFIX-accounts" --item "file://tmp/item1002.json"
$count = aws dynamodb scan --table-name "$PREFIX-accounts" --query "Count" --output text
Save-Ev "01b_dynamo_count.txt" "Count=$count"

# vuln lambda
Push-Location $CODE
if (Test-Path vuln_app.zip) { Remove-Item vuln_app.zip -Force }
& zip.exe -qj vuln_app.zip vuln_app.py
$fn = aws lambda create-function --function-name "$PREFIX-api" --runtime python3.12 --handler vuln_app.handler --zip-file "fileb://vuln_app.zip" --role $ROLE_ARN --timeout 10 --query "FunctionArn" --output text
AwsOk "create-function"
if (-not $fn -or $fn -eq "None") {
  aws lambda update-function-code --function-name "$PREFIX-api" --zip-file "fileb://vuln_app.zip" | Out-Null
  aws lambda wait function-updated --function-name "$PREFIX-api"
  aws lambda update-function-configuration --function-name "$PREFIX-api" --handler vuln_app.handler --role $ROLE_ARN | Out-Null
  aws lambda wait function-updated --function-name "$PREFIX-api"
  $fn = aws lambda get-function --function-name "$PREFIX-api" --query "Configuration.FunctionArn" --output text
}
Pop-Location
Save-Ev "01c_lambda_arn.txt" $fn
Start-Sleep -Seconds 5

# cognito
$POOL_ID = aws cognito-idp create-user-pool --pool-name "$PREFIX-pool" --policies "file://tmp/pwpolicy.json" --query "UserPool.Id" --output text 2>$null
if (-not $POOL_ID -or $POOL_ID -eq "None") {
  Set-Content -Encoding ascii (Join-Path $TMP "pwpolicy.json") '{"PasswordPolicy":{"MinimumLength":8,"RequireUppercase":true,"RequireLowercase":true,"RequireNumbers":true,"RequireSymbols":false}}'
  $POOL_ID = aws cognito-idp create-user-pool --pool-name "$PREFIX-pool" --policies "file://tmp/pwpolicy.json" --query "UserPool.Id" --output text
}
AwsOk "create-user-pool"
$CLIENT_ID = aws cognito-idp create-user-pool-client --user-pool-id $POOL_ID --client-name "$PREFIX-client" --no-generate-secret --explicit-auth-flows ALLOW_USER_PASSWORD_AUTH ALLOW_REFRESH_TOKEN_AUTH --query "UserPoolClient.ClientId" --output text
foreach ($U in @("alice","bob")) {
  aws cognito-idp admin-create-user --user-pool-id $POOL_ID --username $U --message-action SUPPRESS 2>$null | Out-Null
  aws cognito-idp admin-set-user-password --user-pool-id $POOL_ID --username $U --password "Passw0rd!" --permanent | Out-Null
}
Save-Ev "01d_cognito.txt" "pool=$POOL_ID`nclient=$CLIENT_ID"

$ISSUER = "https://cognito-idp.us-east-1.amazonaws.com/$POOL_ID"
$API_ID = aws apigatewayv2 create-api --name "$PREFIX-api" --protocol-type HTTP --query "ApiId" --output text
$AUTH_ID = aws apigatewayv2 create-authorizer --api-id $API_ID --authorizer-type JWT --name cognito --identity-source '$request.header.Authorization' --jwt-configuration "Audience=$CLIENT_ID,Issuer=$ISSUER" --query "AuthorizerId" --output text
$INTEG_ID = aws apigatewayv2 create-integration --api-id $API_ID --integration-type AWS_PROXY --integration-uri "arn:aws:lambda:us-east-1:${ACCT}:function:$PREFIX-api" --payload-format-version "2.0" --query "IntegrationId" --output text
aws apigatewayv2 create-route --api-id $API_ID --route-key "GET /accounts/{id}" --target "integrations/$INTEG_ID" --authorization-type JWT --authorizer-id $AUTH_ID | Out-Null
# HEAD so curl -sI reaches Lambda (lab Ev #6); unused methods still 404
aws apigatewayv2 create-route --api-id $API_ID --route-key "HEAD /accounts/{id}" --target "integrations/$INTEG_ID" --authorization-type JWT --authorizer-id $AUTH_ID | Out-Null
aws apigatewayv2 create-stage --api-id $API_ID --stage-name '$default' --auto-deploy 2>$null | Out-Null
aws lambda add-permission --function-name "$PREFIX-api" --statement-id apigw --action lambda:InvokeFunction --principal apigateway.amazonaws.com --source-arn "arn:aws:execute-api:us-east-1:${ACCT}:${API_ID}/*/*/accounts/*" 2>$null | Out-Null
$ENDPOINT = "https://$API_ID.execute-api.us-east-1.amazonaws.com"
Save-Ev "02_endpoint.txt" $ENDPOINT
@"
ACCT=$ACCT
PREFIX=$PREFIX
ROLE_ARN=$ROLE_ARN
POOL_ID=$POOL_ID
CLIENT_ID=$CLIENT_ID
API_ID=$API_ID
ENDPOINT=$ENDPOINT
"@ | Set-Content -Encoding ascii (Join-Path $ROOT "lab_env.txt")
Start-Sleep -Seconds 10

# Part B
$noTok = curl.exe -s -o NUL -w "no token -> HTTP %{http_code}" "$ENDPOINT/accounts/1002"
$ALICE = aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH --client-id $CLIENT_ID --auth-parameters "USERNAME=alice,PASSWORD=Passw0rd!" --query "AuthenticationResult.IdToken" --output text
$own = curl.exe -s -H "Authorization: $ALICE" "$ENDPOINT/accounts/1001"
$bola = curl.exe -s -H "Authorization: $ALICE" "$ENDPOINT/accounts/1002"
Save-Ev "03_bola.txt" @"
$noTok
ALICE_TOKEN_PREFIX=$($ALICE.Substring(0,[Math]::Min(40,$ALICE.Length)))...
OWN_ACCOUNT=$own
BOLA_LEAK=$bola
"@

$post = curl.exe -s -o NUL -w "POST -> HTTP %{http_code}" -X POST -H "Authorization: $ALICE" "$ENDPOINT/accounts/1001"
$del = curl.exe -s -o NUL -w "DELETE -> HTTP %{http_code}" -X DELETE -H "Authorization: $ALICE" "$ENDPOINT/accounts/1001"
# Corrupt signature segment so JWT authorizer must reject (last-char flip can be a no-op)
$tokParts = $ALICE.Split('.')
$BAD = $tokParts[0] + "." + $tokParts[1] + ".tampered" + $tokParts[2]
$tamp = curl.exe -s -o NUL -w "tampered token -> HTTP %{http_code}" -H "Authorization: $BAD" "$ENDPOINT/accounts/1001"
$parts = $ALICE.Split('.')
$payload = $parts[1].Replace('-','+').Replace('_','/')
while ($payload.Length % 4) { $payload += '=' }
$claimsJson = [Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($payload))
Save-Ev "04_methods_token.txt" @"
$post
$del
$tamp
CLAIMS=$claimsJson
"@

# Part C BOLA-only fix first (full item return for Part D leak demo)
Push-Location $CODE
Copy-Item fixed_app_bola_only.py fixed_app.py -Force
if (Test-Path fixed_app.zip) { Remove-Item fixed_app.zip -Force }
& zip.exe -qj fixed_app.zip fixed_app.py
aws lambda update-function-code --function-name "$PREFIX-api" --zip-file "fileb://fixed_app.zip" | Out-Null
aws lambda wait function-updated --function-name "$PREFIX-api"
aws lambda update-function-configuration --function-name "$PREFIX-api" --handler fixed_app.handler | Out-Null
aws lambda wait function-updated --function-name "$PREFIX-api"
Pop-Location
Start-Sleep -Seconds 5

$ALICE = aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH --client-id $CLIENT_ID --auth-parameters "USERNAME=alice,PASSWORD=Passw0rd!" --query "AuthenticationResult.IdToken" --output text
$fixOwn = curl.exe -s -w "`n<- HTTP %{http_code}" -H "Authorization: $ALICE" "$ENDPOINT/accounts/1001"
$fixBob = curl.exe -s -w "`n<- HTTP %{http_code}" -H "Authorization: $ALICE" "$ENDPOINT/accounts/1002"
Save-Ev "05_bola_fixed.txt" @"
OWN=$fixOwn
BOB=$fixBob
"@

# Part D leak: add sensitive fields while still returning full item
Set-Content -Encoding ascii (Join-Path $TMP "key1001.json") '{"account_id":{"S":"1001"}}'
Set-Content -Encoding ascii (Join-Path $TMP "exprvals.json") '{":n":{"S":"VIP-PHI-REVIEW"},":f":{"N":"0.91"}}'
aws dynamodb update-item --table-name "$PREFIX-accounts" --key "file://tmp/key1001.json" --update-expression "SET internal_note = :n, fraud_score = :f" --expression-attribute-values "file://tmp/exprvals.json"
$leak = curl.exe -s -H "Authorization: $ALICE" "$ENDPOINT/accounts/1001"
Save-Ev "06_partD_leak.txt" $leak

# Final allow-list + headers
Push-Location $CODE
@'
import json, boto3
ddb = boto3.resource("dynamodb")
table = ddb.Table("ia642-lab-accounts")
ALLOWED_FIELDS = ("account_id", "balance", "card_last4")
SECURE_HEADERS = {
    "Content-Type": "application/json",
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'; base-uri 'none'",
    "Cache-Control": "no-store",
}
def handler(event, context):
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    caller = claims.get("cognito:username", "anonymous")
    acct_id = event.get("pathParameters", {}).get("id")
    item = table.get_item(Key={"account_id": acct_id}).get("Item")
    if not item:
        return {"statusCode": 404, "headers": SECURE_HEADERS, "body": json.dumps({"error": "not found"})}
    if item.get("owner") != caller:
        return {"statusCode": 403, "headers": SECURE_HEADERS, "body": json.dumps({"error": "forbidden", "caller": caller})}
    safe = {k: item[k] for k in ALLOWED_FIELDS if k in item}
    return {"statusCode": 200, "headers": SECURE_HEADERS, "body": json.dumps({"caller": caller, "account": safe}, default=str)}
'@ | Set-Content -Encoding ascii fixed_app.py
if (Test-Path fixed_app.zip) { Remove-Item fixed_app.zip -Force }
& zip.exe -qj fixed_app.zip fixed_app.py
aws lambda update-function-code --function-name "$PREFIX-api" --zip-file "fileb://fixed_app.zip" | Out-Null
aws lambda wait function-updated --function-name "$PREFIX-api"
aws lambda update-function-configuration --function-name "$PREFIX-api" --handler fixed_app.handler | Out-Null
aws lambda wait function-updated --function-name "$PREFIX-api"
Pop-Location
Start-Sleep -Seconds 5

$ALICE = aws cognito-idp initiate-auth --auth-flow USER_PASSWORD_AUTH --client-id $CLIENT_ID --auth-parameters "USERNAME=alice,PASSWORD=Passw0rd!" --query "AuthenticationResult.IdToken" --output text
$after = curl.exe -s -H "Authorization: $ALICE" "$ENDPOINT/accounts/1001"
$hdrs = curl.exe -sI -H "Authorization: $ALICE" "$ENDPOINT/accounts/1001"
# fallback if HEAD still not routed: dump GET response headers
if ($hdrs -notmatch "Strict-Transport-Security") {
  $hdrs = curl.exe -sD - -o NUL -H "Authorization: $ALICE" "$ENDPOINT/accounts/1001"
}
Save-Ev "06b_partD_fixed.txt" $after
Save-Ev "06_headers.txt" $hdrs

# diffs for report
Push-Location $CODE
git diff --no-index vuln_app.py fixed_app_bola_only.py 2>$null | Out-File -Encoding utf8 (Join-Path $EV "diff_bola_fix.txt")
git diff --no-index fixed_app_bola_only.py fixed_app.py 2>$null | Out-File -Encoding utf8 (Join-Path $EV "diff_allowlist_headers.txt")
# also simple copies
Copy-Item vuln_app.py (Join-Path $EV "vuln_app.py") -Force
Copy-Item fixed_app_bola_only.py (Join-Path $EV "fixed_app_bola_only.py") -Force
Copy-Item fixed_app.py (Join-Path $EV "fixed_app_final.py") -Force
Pop-Location

# Teardown (skip with SKIP_TEARDOWN=1 to leave live demo up)
if ($env:SKIP_TEARDOWN -eq "1") {
  Save-Ev "07_teardown.txt" "SKIPPED - live demo left running`nENDPOINT=$ENDPOINT`nPOOL_ID=$POOL_ID`nCLIENT_ID=$CLIENT_ID`nAPI_ID=$API_ID"
  Write-Host "LAB COMPLETE (LIVE - teardown skipped)"
  Write-Host "ENDPOINT=$ENDPOINT"
  Write-Host "CLIENT_ID=$CLIENT_ID"
} else {
  aws apigatewayv2 delete-api --api-id $API_ID 2>$null | Out-Null
  aws lambda delete-function --function-name "$PREFIX-api" 2>$null | Out-Null
  aws dynamodb delete-table --table-name "$PREFIX-accounts" 2>$null | Out-Null
  aws cognito-idp delete-user-pool --user-pool-id $POOL_ID 2>$null | Out-Null
  aws iam delete-role-policy --role-name "$PREFIX-role" --policy-name app 2>$null | Out-Null
  Start-Sleep -Seconds 3
  aws iam delete-role --role-name "$PREFIX-role" 2>$null | Out-Null
  Start-Sleep -Seconds 5
  $t1 = aws lambda list-functions --query "Functions[?starts_with(FunctionName,'$PREFIX')].FunctionName" --output text
  $t2 = aws dynamodb list-tables --query "TableNames[?starts_with(@,'$PREFIX')]" --output text
  Save-Ev "07_teardown.txt" "lambda=[$t1]`ndynamo=[$t2]"
  Write-Host "LAB COMPLETE"
}
Get-ChildItem $EV | Format-Table Name,Length
