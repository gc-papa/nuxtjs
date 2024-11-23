from http.server import BaseHTTPRequestHandler, HTTPServer
import requests
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import subprocess
import json

# Cloud Run URL
CLOUD_RUN_URL = "https://nuxtjs-839767914554.europe-west6.run.app"

# Automatically get an identity token using gcloud
def get_identity_token():
    result = subprocess.run(
        ["gcloud", "auth", "print-identity-token"],
        stdout=subprocess.PIPE,
        text=True
    )
    return result.stdout.strip()

parsed_url = urlparse(CLOUD_RUN_URL)
CLOUD_RUN_HOST = parsed_url.netloc

class ProxyHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Generate a new ID token for each request
        ID_TOKEN = get_identity_token()

        headers = {
            'Authorization': f'Bearer {ID_TOKEN}',
            'Host': CLOUD_RUN_HOST,
            'User-Agent': 'Python-requests/2.27.1'
        }

        try:
            session = requests.Session()
            retry = Retry(connect=5, backoff_factor=0.5)
            adapter = HTTPAdapter(max_retries=retry)
            session.mount('https://', adapter)

            # Make a request to Cloud Run
            response = session.get(
                CLOUD_RUN_URL + self.path,
                headers=headers,
                verify='/etc/ssl/certs/ca-certificates.crt',
                timeout=30
            )

            # Send response to client
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                if key.lower() != 'transfer-encoding':  # Preventing issues with chunked encoding
                    self.send_header(key, value)

            # Add CORS headers to support browser access
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')

            self.end_headers()
            self.wfile.write(response.content)

        except requests.exceptions.RequestException as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_OPTIONS(self):
        """Handle CORS preflight requests."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        self.end_headers()

def run(server_class=HTTPServer, handler_class=ProxyHTTPRequestHandler):
    server_address = ('', 8080)  # Listen on localhost, port 8080
    httpd = server_class(server_address, handler_class)
    print('Starting proxy server on port 8080...')
    httpd.serve_forever()

if __name__ == '__main__':
    run()
