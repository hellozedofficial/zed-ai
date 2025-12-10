import boto3
import os
from dotenv import load_dotenv

load_dotenv()

bedrock = boto3.client(
    service_name='bedrock',
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

print('Checking available Bedrock models in your account...\n')

try:
    response = bedrock.list_foundation_models()
    
    # Filter for text/chat models
    models = []
    for model in response.get('modelSummaries', []):
        if 'TEXT' in model.get('outputModalities', []) and model.get('modelLifecycle', {}).get('status') == 'ACTIVE':
            models.append({
                'id': model['modelId'],
                'name': model['modelName'],
                'provider': model['providerName']
            })
    
    # Group by provider
    providers = {}
    for model in models:
        provider = model['provider']
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(model)
    
    print(f'Total available models: {len(models)}\n')
    
    for provider, provider_models in sorted(providers.items()):
        print(f'\n{provider}:')
        print('-' * 50)
        for model in provider_models:
            print(f'  • {model["name"]}')
            print(f'    ID: {model["id"]}')
            print()
            
except Exception as e:
    print(f'Error: {e}')
