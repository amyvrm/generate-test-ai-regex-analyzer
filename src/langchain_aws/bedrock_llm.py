import boto3
import json

class BedrockLLM:
    """
    Minimal BedrockLLM wrapper for AWS Bedrock text generation.
    """
    def __init__(self, credentials_profile_name=None, provider=None, client=None, model_id=None, model_kwargs=None):
        self.credentials_profile_name = credentials_profile_name
        self.provider = provider
        self.client = client or boto3.client('bedrock-runtime')
        self.model_id = model_id
        self.model_kwargs = model_kwargs or {}

    def invoke(self, input):
        body = {
            "prompt": input,
            **self.model_kwargs
        }
        response = self.client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body)
        )
        result = response.get("body")
        # If result is a StreamingBody, read and decode it
        if hasattr(result, "read"):
            result = result.read().decode("utf-8")
        elif isinstance(result, bytes):
            result = result.decode("utf-8")
        # Parse the JSON string to extract the actual output
        try:
            result_json = json.loads(result)
            return result_json["outputs"][0]["text"]
            # for key in ["output", "result", "generation", "body", "text"]:
            #     if key in result_json:
            #         return result_json[key]
            # return json.dumps(result_json)
        except Exception:
            return result
