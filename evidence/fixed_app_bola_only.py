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
    # FIX (ASVS v5.0.0-8.2.2): object-level authorization -- return the record
    # only if the authenticated caller actually owns it.
    if item.get("owner") != caller:
        return {"statusCode": 403,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "forbidden", "caller": caller})}
    return {"statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"caller": caller, "account": item}, default=str)}
