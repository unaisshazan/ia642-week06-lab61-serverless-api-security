import json, boto3
ddb = boto3.resource("dynamodb")
table = ddb.Table("ia642-lab-accounts")

def handler(event, context):
    claims = event.get("requestContext", {}).get("authorizer", {}).get("jwt", {}).get("claims", {})
    caller = claims.get("cognito:username", "anonymous")
    acct_id = event.get("pathParameters", {}).get("id")
    item = table.get_item(Key={"account_id": acct_id}).get("Item")
    if not item:
        return {"statusCode": 404, "body": json.dumps({"error": "not found"})}
    # VULNERABILITY (OWASP API1:2023 BOLA): returns the record to ANY
    # authenticated caller -- no check that item["owner"] == caller.
    return {"statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"caller": caller, "account": item}, default=str)}
