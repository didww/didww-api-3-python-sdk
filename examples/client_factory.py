import os
import sys

from didww.client import DidwwClient
from didww.configuration import Environment


def create_client():
    api_key = os.environ.get("DIDWW_API_KEY")
    if not api_key:
        print("DIDWW_API_KEY environment variable is required", file=sys.stderr)
        sys.exit(1)
    return DidwwClient(api_key=api_key, environment=Environment.SANDBOX)
