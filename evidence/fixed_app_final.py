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
