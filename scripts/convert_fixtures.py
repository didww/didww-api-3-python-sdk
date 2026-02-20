#!/usr/bin/env python3
"""Convert Java SDK JSON fixtures to VCR.py YAML cassettes."""

import json
import os
import yaml

JAVA_FIXTURES = os.path.join(
    os.path.dirname(__file__),
    "../../didww-api-3-java-sdk/src/test/resources/fixtures",
)
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "../tests/fixtures")
BASE_URL = "https://sandbox-api.didww.com/v3"

COMMON_HEADERS = {
    "Accept": ["application/vnd.api+json"],
    "Api-Key": ["test-api-key"],
    "Content-Type": ["application/vnd.api+json"],
}

RESPONSE_HEADERS = {
    "Content-Type": ["application/vnd.api+json"],
}


def load_json(path):
    with open(path) as f:
        return f.read().strip()


def make_interaction(method, uri, request_body, response_body, status_code, status_msg):
    req = {
        "body": request_body,
        "headers": COMMON_HEADERS,
        "method": method,
        "uri": uri,
    }
    resp = {
        "body": {"string": response_body},
        "headers": RESPONSE_HEADERS,
        "status": {"code": status_code, "message": status_msg},
    }
    return {"request": req, "response": resp}


def write_cassette(output_path, interactions):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    cassette = {"interactions": interactions, "version": 1}
    with open(output_path, "w") as f:
        yaml.dump(cassette, f, default_flow_style=False, sort_keys=False)


def get_first_id(fixture_path):
    """Extract the first resource ID from a show/create fixture."""
    with open(fixture_path) as f:
        data = json.load(f)
    if "data" in data:
        d = data["data"]
        if isinstance(d, dict):
            return d.get("id", "unknown-id")
        if isinstance(d, list) and d:
            return d[0].get("id", "unknown-id")
    return "unknown-id"


def convert_resource(resource_dir, resource_name):
    """Convert a single Java fixture directory to VCR cassettes."""
    files = set(os.listdir(resource_dir))
    endpoint = f"{BASE_URL}/{resource_name}"
    out_dir = os.path.join(OUTPUT_DIR, resource_name)

    # INDEX -> list.yaml
    if "index.json" in files:
        body = load_json(os.path.join(resource_dir, "index.json"))
        interaction = make_interaction("GET", endpoint, None, body, 200, "OK")
        write_cassette(os.path.join(out_dir, "list.yaml"), [interaction])

    # SHOW -> show.yaml
    if "show.json" in files:
        show_path = os.path.join(resource_dir, "show.json")
        rid = get_first_id(show_path)
        body = load_json(show_path)
        interaction = make_interaction("GET", f"{endpoint}/{rid}", None, body, 200, "OK")
        write_cassette(os.path.join(out_dir, "show.yaml"), [interaction])

    # CREATE -> create.yaml
    if "create.json" in files:
        resp_body = load_json(os.path.join(resource_dir, "create.json"))
        req_body = None
        if "create_request.json" in files:
            req_body = load_json(os.path.join(resource_dir, "create_request.json"))
        interaction = make_interaction("POST", endpoint, req_body, resp_body, 201, "Created")
        write_cassette(os.path.join(out_dir, "create.yaml"), [interaction])

    # DELETE -> delete.yaml (use ID from show or create fixture)
    if "delete.json" in files:
        del_path = os.path.join(resource_dir, "delete.json")
        del_body = load_json(del_path)
        # Try to get ID from the delete fixture
        try:
            del_data = json.loads(del_body)
            rid = del_data.get("data", {}).get("id", "unknown-id")
        except (json.JSONDecodeError, AttributeError):
            rid = "unknown-id"
        interaction = make_interaction("DELETE", f"{endpoint}/{rid}", None, del_body, 200, "OK")
        write_cassette(os.path.join(out_dir, "delete.yaml"), [interaction])

    # Numbered creates (create_1.json, create_2.json, etc.)
    for f in sorted(files):
        if f.startswith("create_") and f.endswith(".json") and f != "create_request.json":
            suffix = f.replace("create_", "").replace(".json", "")
            # Try to find matching request
            req_file = f"create_request_{suffix}.json" if f"create_request_{suffix}.json" in files else None
            resp_body = load_json(os.path.join(resource_dir, f))
            req_body = None
            if req_file:
                req_body = load_json(os.path.join(resource_dir, req_file))
            interaction = make_interaction("POST", endpoint, req_body, resp_body, 201, "Created")
            write_cassette(os.path.join(out_dir, f"create_{suffix}.yaml"), [interaction])

    # Numbered request-only creates (create_request_xxx.json without matching create_xxx.json)
    for f in sorted(files):
        if f.startswith("create_request_") and f.endswith(".json"):
            suffix = f.replace("create_request_", "").replace(".json", "")
            resp_file = f"create_{suffix}.json"
            if resp_file not in files:
                # Create request without specific response, use generic create.json
                req_body = load_json(os.path.join(resource_dir, f))
                resp_body = load_json(os.path.join(resource_dir, "create.json")) if "create.json" in files else "{}"
                interaction = make_interaction("POST", endpoint, req_body, resp_body, 201, "Created")
                write_cassette(os.path.join(out_dir, f"create_{suffix}.yaml"), [interaction])

    # UPDATE -> update.yaml
    if "update.json" in files:
        resp_body = load_json(os.path.join(resource_dir, "update.json"))
        req_body = None
        if "update_request.json" in files:
            req_body = load_json(os.path.join(resource_dir, "update_request.json"))
        # Try to get ID from update response
        try:
            upd_data = json.loads(resp_body)
            if "data" in upd_data:
                rid = upd_data["data"].get("id", "unknown-id")
            else:
                rid = "unknown-id"
        except (json.JSONDecodeError, AttributeError):
            rid = "unknown-id"
        interaction = make_interaction("PATCH", f"{endpoint}/{rid}", req_body, resp_body, 200, "OK")
        write_cassette(os.path.join(out_dir, "update.yaml"), [interaction])

    # Numbered updates (update_1.json, update_2.json, etc.)
    for f in sorted(files):
        if f.startswith("update_") and f.endswith(".json") and f != "update_request.json":
            suffix = f.replace("update_", "").replace(".json", "")
            resp_body = load_json(os.path.join(resource_dir, f))
            try:
                upd_data = json.loads(resp_body)
                if "data" in upd_data:
                    rid = upd_data["data"].get("id", "unknown-id")
                elif "errors" in upd_data:
                    rid = "unknown-id"
                else:
                    rid = "unknown-id"
            except (json.JSONDecodeError, AttributeError):
                rid = "unknown-id"
            # Determine status from content
            try:
                content = json.loads(resp_body)
                if "errors" in content:
                    status_code, status_msg = 422, "Unprocessable Entity"
                else:
                    status_code, status_msg = 200, "OK"
            except (json.JSONDecodeError, AttributeError):
                status_code, status_msg = 200, "OK"
            interaction = make_interaction("PATCH", f"{endpoint}/{rid}", None, resp_body, status_code, status_msg)
            write_cassette(os.path.join(out_dir, f"update_{suffix}.yaml"), [interaction])

    # Numbered shows (show_4.json, show_6.json, etc.)
    for f in sorted(files):
        if f.startswith("show_") and f.endswith(".json"):
            suffix = f.replace("show_", "").replace(".json", "")
            show_path = os.path.join(resource_dir, f)
            body = load_json(show_path)
            try:
                show_data = json.loads(body)
                if "data" in show_data:
                    rid = show_data["data"].get("id", "unknown-id")
                else:
                    rid = "unknown-id"
            except (json.JSONDecodeError, AttributeError):
                rid = "unknown-id"
            interaction = make_interaction("GET", f"{endpoint}/{rid}", None, body, 200, "OK")
            write_cassette(os.path.join(out_dir, f"show_{suffix}.yaml"), [interaction])

    # Numbered index files (index_2.json, etc.)
    for f in sorted(files):
        if f.startswith("index_") and f.endswith(".json"):
            suffix = f.replace("index_", "").replace(".json", "")
            body = load_json(os.path.join(resource_dir, f))
            interaction = make_interaction("GET", endpoint, None, body, 200, "OK")
            write_cassette(os.path.join(out_dir, f"list_{suffix}.yaml"), [interaction])


def main():
    if not os.path.isdir(JAVA_FIXTURES):
        print(f"Java fixtures directory not found: {JAVA_FIXTURES}")
        return

    for name in sorted(os.listdir(JAVA_FIXTURES)):
        resource_dir = os.path.join(JAVA_FIXTURES, name)
        if os.path.isdir(resource_dir):
            print(f"Converting: {name}")
            convert_resource(resource_dir, name)

    print(f"\nDone! Cassettes written to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
