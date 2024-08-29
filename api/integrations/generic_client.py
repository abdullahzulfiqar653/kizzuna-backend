import requests

safe_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~%")


class GenericAPIClient:
    """
    A generic API client for making HTTP requests to a specified base URL with an API key.

    Usage:
    1. Create an instance of the `GenericAPIClient` class by providing the base URL and API key.
    2. Use the instance to make API requests by calling the desired endpoint as an attribute.

    Example:
    To make a GET request to the `/users/{user_id}/resources` endpoint:

    ```
    client = GenericAPIClient("https://api.example.com", "your-api-key")
    response = client.users(user_id).resources().get()
    print(response.json())
    ```

    Args:
        base_url (str): The base URL of the API.
        api_key (str): The API key used for authentication.

    Attributes:
        api_key (str): The API key used for authentication.
        base_url (str): The base URL of the API.
        session (requests.Session): The session object used for making HTTP requests.

    """

    def __init__(self, base_url, headers, trailing_slash=True):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update(headers)
        self.trailing_slash = trailing_slash

    def __getattr__(self, name):
        return getattr(APIEndpoint(self, ""), name)


class APIEndpoint:
    def __init__(
        self, client: GenericAPIClient, path="", params=None, underscore=False
    ):
        self.client = client
        self.path = path
        self.params = params or {}
        self.underscore = underscore

    def __getattr__(self, name):
        if not self.underscore:
            name = name.replace("_", "-")
        return APIEndpoint(self.client, f"{self.path}/{name}")

    def __call__(self, arg=None):
        if isinstance(arg, str):
            # Check if the argument is safe to add as a URL parameter
            if self._is_safe_url_param(arg):
                new_path = f"{self.path}/{arg}"
            else:
                raise ValueError("Unsafe URL parameter")
        elif arg is None:
            return self
        else:
            raise ValueError("Invalid argument type")

        return APIEndpoint(self.client, new_path)

    def _is_safe_url_param(self, param):
        # Implement your logic to check if the parameter is safe to add as a URL parameter
        # Return True if safe, False otherwise
        # Example implementation:
        return set(param).issubset(safe_chars)

    def get(self, **query_params):
        return self._make_request("GET", query_params=query_params)

    def post(self, **data):
        return self._make_request("POST", json=data)

    def put(self, **data):
        return self._make_request("PUT", json=data)

    def patch(self, **data):
        return self._make_request("PATCH", json=data)

    def delete(self):
        return self._make_request("DELETE")

    def _make_request(self, method, query_params=None, json=None):
        url = f"{self.client.base_url}{self.path.format(**self.params)}"
        if self.client.trailing_slash:
            url = url.rstrip("/") + "/"
        response = self.client.session.request(
            method, url, params=query_params, json=json
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise requests.exceptions.HTTPError(f"{e}\nResponse: {response.text}")
        try:
            return response.json()
        except:
            return response.text
