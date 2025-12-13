import json
from lemonsqueezy import LemonSqueezyService

if __name__ == "__main__":
    with open("sample_webhook.json", "r") as f:
        payload = json.load(f)
    svc = LemonSqueezyService()
    result = svc.process_webhook_event(payload)
    print(result)