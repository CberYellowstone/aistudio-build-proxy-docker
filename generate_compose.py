import os
import sys

import yaml
from dotenv import load_dotenv


def str_to_bool(s):
    return s.lower() in ["true", "1", "t", "y", "yes"]


def generate_compose_file():
    """
    Generates a docker-compose.yml file based on settings in the .env file,
    and conditionally adds and configures a tinyproxy service with health checks.
    """
    load_dotenv()

    try:
        instances = int(os.getenv("INSTANCES", 1))
        startup_url = os.getenv("STARTUP_URL", "")
        use_tinyproxy = str_to_bool(os.getenv("USE_TINYPROXY", "false"))
        vnc_password = os.getenv("VNC_PASSWORD", "password")
        vnc_secure = str_to_bool(os.getenv("VNC_SECURE", "false"))
        display_width = os.getenv("DISPLAY_WIDTH", "1280")
        display_height = os.getenv("DISPLAY_HEIGHT", "720")
        dark_mode = os.getenv("DARK_MODE", "1")
        use_monitoring = str_to_bool(os.getenv("WITH_MONITORING", "false"))
        proxy_auth_key = os.getenv("PROXY_AUTH_KEY", "")
    except (ValueError, TypeError) as e:
        print(f"Error parsing .env file: {e}")
        sys.exit(1)

    try:
        with open("docker-compose.base.yml", "r") as f:
            compose_data = yaml.safe_load(f)
        with open("firefox.service.template.yml", "r") as f:
            firefox_template = yaml.safe_load(f)
        if use_tinyproxy:
            with open("tinyproxy.service.template.yml", "r") as f:
                tinyproxy_template = yaml.safe_load(f)
    except FileNotFoundError as e:
        print(f"Error: Template file not found: {e}")
        sys.exit(1)

    proxy_service = compose_data["services"]["proxy"]
    proxy_service["ports"] = ["5345:5345"]
    if "environment" not in proxy_service:
        proxy_service["environment"] = []
    proxy_service["environment"].append(f"PROXY_AUTH_KEY={proxy_auth_key}")

    if use_tinyproxy:
        compose_data["services"]["tinyproxy"] = tinyproxy_template

    base_vnc_port = 5900

    for i in range(1, instances + 1):
        service_name = f"firefox-{i}"
        vnc_port = base_vnc_port + i

        service_config = yaml.safe_load(yaml.dump(firefox_template))

        # --- Set conditional depends_on with healthcheck ---
        depends_on_config = {"proxy": {"condition": "service_healthy"}}
        if use_tinyproxy:
            depends_on_config["tinyproxy"] = {"condition": "service_healthy"}
        service_config["depends_on"] = depends_on_config

        service_config["container_name"] = f"firefox-vnc-{i}"
        service_config["volumes"] = [f"firefox_data_{i}:/config"]

        env_vars = []
        env_vars.append(f"VNC_LISTENING_PORT={vnc_port}")
        env_vars.append("WEB_LISTENING_PORT=-1")
        env_vars.append(f"FF_OPEN_URL={startup_url}")
        env_vars.append(f"VNC_PASSWORD={vnc_password}")
        env_vars.append(f"DISPLAY_WIDTH={display_width}")
        env_vars.append(f"DISPLAY_HEIGHT={display_height}")
        env_vars.append(f"DARK_MODE={dark_mode}")
        if vnc_secure:
            env_vars.append("SECURE_CONNECTION_VNC_METHOD=TLS")
            env_vars.append("SECURE_CONNECTION=1")

        if use_tinyproxy:
            env_vars.append("FF_PREF_PROXY_TYPE=network.proxy.type=1")
            env_vars.append('FF_PREF_PROXY_HTTP_HOST=network.proxy.http="tinyproxy"')
            env_vars.append("FF_PREF_PROXY_HTTP_PORT=network.proxy.http_port=8888")
            env_vars.append('FF_PREF_PROXY_SSL_HOST=network.proxy.ssl="tinyproxy"')
            env_vars.append("FF_PREF_PROXY_SSL_PORT=network.proxy.ssl_port=8888")
            env_vars.append(
                'FF_PREF_NO_PROXY_ON=network.proxy.no_proxies_on="localhost,127.0.0.1"'
            )
        else:
            # Explicitly set no proxy
            env_vars.append("FF_PREF_PROXY_TYPE=network.proxy.type=0")

        service_config["environment"] = env_vars
        compose_data["services"][service_name] = service_config
        proxy_service["ports"].append(f"{vnc_port}:{vnc_port}")

    compose_data["volumes"] = {
        f"firefox_data_{i}": None for i in range(1, instances + 1)
    }

    # --- Conditionally add monitoring stack ---
    if use_monitoring:
        monitoring_services = {
            "prometheus": {
                "image": "prom/prometheus:v2.37.0",
                "container_name": "prometheus",
                "restart": "unless-stopped",
                "volumes": [
                    "./monitoring/prometheus:/etc/prometheus",
                    "prometheus_data:/prometheus",
                ],
                "command": ["--config.file=/etc/prometheus/prometheus.yml"],
                "ports": ["9090:9090"],
            }
        }
        compose_data["services"].update(monitoring_services)

        # Merge top-level volumes
        monitoring_volumes = {"prometheus_data": None}
        if "volumes" not in compose_data:
            compose_data["volumes"] = {}
        compose_data["volumes"].update(monitoring_volumes)

        # Define and assign network
        compose_data["networks"] = {"gemini_proxy_network": {"driver": "bridge"}}
        for service_name, service_config in compose_data["services"].items():
            if not service_name.startswith("firefox-"):
                service_config["networks"] = ["gemini_proxy_network"]

    try:
        with open("docker-compose.yml", "w") as f:
            yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)
        print(
            f"Successfully generated 'docker-compose.yml' with {instances} firefox instance(s)."
        )
        if use_tinyproxy:
            print("Upstream proxy via tinyproxy is ENABLED.")
        else:
            print("Upstream proxy is DISABLED.")
        if use_monitoring:
            print("Monitoring stack (Prometheus only) is ENABLED.")
        else:
            print("Monitoring stack is DISABLED.")
    except IOError as e:
        print(f"Error writing to output file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    generate_compose_file()
