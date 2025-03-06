# route_backend_settings.py

from config import *
from functions_documents import *
from functions_authentication import *
from functions_settings import *

def register_route_backend_settings(app):
    @app.route('/api/admin/settings/test_connection', methods=['POST'])
    @login_required
    @admin_required
    def test_connection():
        """
        Receives JSON payload with { test_type: "...", ... } containing ephemeral
        data from admin_settings.js. Uses that data to attempt an actual connection
        to GPT, Embeddings, etc., and returns success/failure.
        """
        data = request.get_json(force=True)
        test_type = data.get('test_type', '')

        try:
            if test_type == 'gpt':
                return _test_gpt_connection(data)

            elif test_type == 'embedding':
                return _test_embedding_connection(data)

            elif test_type == 'image':
                return _test_image_gen_connection(data)

            elif test_type == 'safety':
                return _test_safety_connection(data)

            elif test_type == 'web_search':
                return _test_web_search_connection(data)

            elif test_type == 'azure_ai_search':
                return _test_azure_ai_search_connection(data)

            elif test_type == 'azure_doc_intelligence':
                return _test_azure_doc_intelligence_connection(data)

            elif test_type == 'chunking_api':
                # If you have a chunking API test, implement it here.
                return jsonify({'message': 'Chunking API connection successful'}), 200

            else:
                return jsonify({'error': f'Unknown test_type: {test_type}'}), 400

        except Exception as e:
            return jsonify({'error': str(e)}), 500


def _test_gpt_connection(payload):
    """Attempt to connect to GPT using ephemeral settings from the admin UI."""
    enable_apim = payload.get('enable_apim', False)
    selected_model = payload.get('selected_model') or {}
    system_message = {
        'role': 'system',
        'content': f"Testing access."
    }

    # Decide GPT model
    if enable_apim:
        apim_data = payload.get('apim', {})
        endpoint = apim_data.get('endpoint')
        api_version = apim_data.get('api_version')
        gpt_model = apim_data.get('deployment')
        subscription_key = apim_data.get('subscription_key')

        gpt_client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=subscription_key
        )
    else:
        direct_data = payload.get('direct', {})
        endpoint = direct_data.get('endpoint')
        api_version = direct_data.get('api_version')
        gpt_model = selected_model.get('deploymentName')

        if direct_data.get('auth_type') == 'managed_identity':
            token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
            
            gpt_client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=endpoint,
                azure_ad_token_provider=token_provider
            )
        else:
            key = direct_data.get('key')

            gpt_client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=endpoint,
                api_key=key
            )

    try:
        response = gpt_client.chat.completions.create(
            model=gpt_model,
            messages=[system_message]
        )
        if response:
            return jsonify({'message': 'GPT connection successful'}), 200
    except Exception as e:
        print(str(e))
        return jsonify({'error': f'Error generating model response: {str(e)}'}), 500


def _test_embedding_connection(payload):
    """Attempt to connect to Embeddings using ephemeral settings from the admin UI."""
    enable_apim = payload.get('enable_apim', False)
    selected_model = payload.get('selected_model') or {}
    text = "Test text for embedding connection."

    if enable_apim:
        apim_data = payload.get('apim', {})
        endpoint = apim_data.get('endpoint')
        api_version = apim_data.get('api_version')
        embedding_model = apim_data.get('deployment')
        subscription_key = apim_data.get('subscription_key')

        embedding_client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=subscription_key
        )
    else:
        direct_data = payload.get('direct', {})
        endpoint = direct_data.get('endpoint')
        api_version = direct_data.get('api_version')
        embedding_model = selected_model.get('deploymentName')

        if direct_data.get('auth_type') == 'managed_identity':
            token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
            
            embedding_client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=endpoint,
                azure_ad_token_provider=token_provider
            )
        else:
            key = direct_data.get('key')

            embedding_client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=endpoint,
                api_key=key
            )
    try:
        response = embedding_client.embeddings.create(
            model=embedding_model,
            input=text
        )

        if response:
            return jsonify({'message': 'Embedding connection successful'}), 200
    except Exception as e:
        print(str(e))
        return jsonify({'error': f'Error generating embedding response: {str(e)}'}), 500
    

def _test_image_gen_connection(payload):
    """Attempt to connect to an Image Generation endpoint using ephemeral settings."""
    enable_apim = payload.get('enable_apim', False)
    selected_model = payload.get('selected_model') or {}
    prompt = "A scenic mountain at sunrise"

    if enable_apim:
        apim_data = payload.get('apim', {})
        endpoint = apim_data.get('endpoint')
        api_version = apim_data.get('api_version')
        image_gen_model = apim_data.get('deployment')
        subscription_key = apim_data.get('subscription_key')

        image_gen_client = AzureOpenAI(
            api_version=api_version,
            azure_endpoint=endpoint,
            api_key=subscription_key
        )
    else:
        direct_data = payload.get('direct', {})
        endpoint = direct_data.get('endpoint')
        api_version = direct_data.get('api_version')
        image_gen_model = selected_model.get('deploymentName')

        if direct_data.get('auth_type') == 'managed_identity':
            token_provider = get_bearer_token_provider(DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
            
            image_gen_client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=endpoint,
                azure_ad_token_provider=token_provider
            )
        else:
            key = direct_data.get('key')

            image_gen_client = AzureOpenAI(
                api_version=api_version,
                azure_endpoint=endpoint,
                api_key=key
            )
    try:
        response = image_gen_client.images.generate(
            prompt=prompt,
            n=1,
            model=image_gen_model
        )
        if response:
            return jsonify({'message': 'Image generation connection successful'}), 200
    except Exception as e:
        print(str(e))
        return jsonify({'error': f'Error generating model response: {str(e)}'}), 500


def _test_safety_connection(payload):
    """Attempt to connect to a content safety endpoint using ephemeral settings."""
    enabled = payload.get('enabled', False)
    if not enabled:
        # If the user toggled content safety off, just return success
        return jsonify({'message': 'Content Safety is disabled, skipping test'}), 200

    enable_apim = payload.get('enable_apim', False)

    if enable_apim:
        apim_data = payload.get('apim', {})
        endpoint = apim_data.get('endpoint')
        subscription_key = apim_data.get('subscription_key')

        content_safety_client = ContentSafetyClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(subscription_key)
        )
    else:
        direct_data = payload.get('direct', {})
        endpoint = direct_data.get('endpoint')
        key = direct_data.get('key')

        if direct_data.get('auth_type') == 'managed_identity':
            
            content_safety_client = ContentSafetyClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential()
            )
        else:
            content_safety_client = ContentSafetyClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key)
            )

    try:     
        user_message = "Test message for content safety connection."
        request_obj = AnalyzeTextOptions(text=user_message)
        cs_response = content_safety_client.analyze_text(request_obj)

        if cs_response:
            return jsonify({'message': 'Safety connection successful'}), 200
    except Exception as e:
        return jsonify({'error': f'Safety connection error: {str(e)}'}), 500


def _test_web_search_connection(payload):
    """Attempt to connect to Bing (or your APIM-protected) web search endpoint."""
    enabled = payload.get('enabled', False)
    if not enabled:
        return jsonify({'message': 'Web Search is disabled, skipping test'}), 200

    enable_apim = payload.get('enable_apim', False)

    if enable_apim:
        apim_data = payload.get('apim', {})
        endpoint = apim_data.get('endpoint')
        subscription_key = apim_data.get('subscription_key')
        # deployment, api_version, etc. if relevant
        url = f"{endpoint.rstrip('/')}/bing/v7.0/search"
        headers = {
            'Ocp-Apim-Subscription-Key': subscription_key
        }
        params = { 'q': 'Test' }
    else:
        direct_data = payload.get('direct', {})
        # For direct Bing calls, you typically do something like:
        key = direct_data.get('key')
        url = "https://api.bing.microsoft.com/v7.0/search"
        headers = {
            'Ocp-Apim-Subscription-Key': key
        }
        params = { 'q': 'Test' }

    resp = requests.get(url, headers=headers, params=params, timeout=10)
    if resp.status_code == 200:
        return jsonify({'message': 'Web search connection successful'}), 200
    else:
        raise Exception(f"Web search connection error: {resp.status_code} - {resp.text}")


def _test_azure_ai_search_connection(payload):
    """Attempt to connect to Azure Cognitive Search (or APIM-wrapped)."""
    enable_apim = payload.get('enable_apim', False)

    if enable_apim:
        apim_data = payload.get('apim', {})
        endpoint = apim_data.get('endpoint')
        subscription_key = apim_data.get('subscription_key')

        content_safety_client = ContentSafetyClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(subscription_key)
        )
    else:
        direct_data = payload.get('direct', {})
        endpoint = direct_data.get('endpoint')
        key = direct_data.get('key')

        if direct_data.get('auth_type') == 'managed_identity':
            
            content_safety_client = ContentSafetyClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential()
            )
        else:
            content_safety_client = ContentSafetyClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key)
            )

    if enable_apim:
        apim_data = payload.get('apim', {})
        endpoint = apim_data.get('endpoint')  # e.g. https://my-apim.azure-api.net/search
        subscription_key = apim_data.get('subscription_key')
        url = f"{endpoint.rstrip('/')}/indexes?api-version=2023-11-01"
        headers = {
            'api-key': subscription_key,
            'Content-Type': 'application/json'
        }
    else:
        direct_data = payload.get('direct', {})
        endpoint = direct_data.get('endpoint')  # e.g. https://<searchservice>.search.windows.net
        key = direct_data.get('key')
        url = f"{endpoint.rstrip('/')}/indexes?api-version=2023-11-01"
        headers = {
            'api-key': key,
            'Content-Type': 'application/json'
        }

    # A small GET to /indexes to verify we have connectivity
    resp = requests.get(url, headers=headers, timeout=10)
    if resp.status_code == 200:
        return jsonify({'message': 'Azure AI search connection successful'}), 200
    else:
        raise Exception(f"Azure AI search connection error: {resp.status_code} - {resp.text}")


def _test_azure_doc_intelligence_connection(payload):
    """Attempt to connect to Azure Form Recognizer / Document Intelligence."""
    enable_apim = payload.get('enable_apim', False)

    enable_apim = payload.get('enable_apim', False)

    if enable_apim:
        apim_data = payload.get('apim', {})
        endpoint = apim_data.get('endpoint')
        subscription_key = apim_data.get('subscription_key')

        document_intelligence_client = DocumentAnalysisClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(subscription_key)
        )
    else:
        direct_data = payload.get('direct', {})
        endpoint = direct_data.get('endpoint')
        key = direct_data.get('key')

        if direct_data.get('auth_type') == 'managed_identity':
            
            document_intelligence_client = DocumentAnalysisClient(
                endpoint=endpoint,
                credential=DefaultAzureCredential()
            )
        else:
            document_intelligence_client = DocumentAnalysisClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(key)
            )
    
    poller = document_intelligence_client.begin_analyze_document_from_url(
        model_id="prebuilt-read",
        document_url="https://github.com/RetroBurnCloud/images/blob/5121c601bc61f9806f0bac7783c44352fd185998/Microsoft_Terms_of_Use.pdf"
    )

    max_wait_time = 600
    start_time = time.time()

    while True:
        status = poller.status()
        if status in ["succeeded", "failed", "canceled"]:
            break
        if time.time() - start_time > max_wait_time:
            raise TimeoutError("Document analysis took too long.")
        time.sleep(30)

    if status == "succeeded":
        return jsonify({'message': 'Azure document intelligence connection successful'}), 200
    else:
        return jsonify({'error': f"Document Intelligence error: {status}"}), 500