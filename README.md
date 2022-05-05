# Tasmota Shelly Plug to InfluxDB Script: Dennis Edition

Based upon this article: https://diyi0t.com/visualize-mqtt-data-with-influxdb-and-grafana

Updated with the following changes:
- Parse multiple datasets based on so called `targets`
- Configuration via JSON file: see the `example` directory
- Automated build of Docker image via GitHub Actions available at<br/>[`ghcr.io/thetredev/tasmota-shelly-plug-influx`](https://ghcr.io/thetredev/tasmota-shelly-plug-influx)

## Running locally
```bash
# 1. Clone the repository and change into the cloned directory
git clone https://github.com/thetredev/tasmota-shelly-plug-influx.git
cd tasmota-shelly-plug-influx

# 2. Copy `example/shelly2influxdb.json` as `config/shelly2influxdb.json` and edit it to suit your environment
mkdir -p config
cp example/shelly2influxdb.json config/shelly2influxdb.json
nano config/shelly2influxdb.json

# 3. Run the script:
python3 shelly2influxdb.py
```

## Running the Docker container
A few words on the container environment: The script checks for whether it's running as container or not as follows:
- Check for the existence of `/run/.containerenv` &rarr; indicates that `podman` has run the container
- Check for the existence of `/.dockerenv` &rarr; indicates `docker` has run the container
- Check for any hints of `docker` in the file `/proc/self/cgroup` (as last resort) &rarr; indicates `docker` has run the container

If all those checks fail, then the script will (must) assume that it's not running inside a container environment. See the function `is_container()` inside the script for implementation details.

Depending on the outcome of those checks, it looks for the config file in different locations:
- As container: `/config/shelly2influxdb.json`
- Locally: `<current dir (pwd)>/config/shelly2influxdb.json`

With all that out of the way, this is how you run the container properly:
```bash
# 1. Create a new directory to work in
mkdir -p ~/shelly2influxdb
cd ~/shelly2influxdb

# 2. Download the example shelly2influxdb.json from the GitHub repository:
wget https://raw.githubusercontent.com/thetredev/tasmota-shelly-plug-influx/main/example/shelly2influxdb.json

# 3. Edit the config file to suit your environment
nano shelly2influxdb.json

# 4. Run the Docker container
docker run --rm \
    -v $(pwd)/shelly2influxdb.json:/config/shelly2influxdb.json:ro \
    ghcr.io/thetredev/tasmota-shelly-plug-influx:latest
```

Needless to say, make sure to replace `:latest` with the image tag you want to run.

## Docker Compose: Minimal example
See the `example` directory.

## Building the Docker Image
```bash
# 1. Clone the repository and change into the cloned directory:
git clone https://github.com/thetredev/tasmota-shelly-plug-influx.git
cd tasmota-shelly-plug-influx

# 2. Set resulting image ID
export DOCKER_IMAGE_ID="your-image:tag"

# 3. Build it using Docker CLI
docker build -t ${DOCKER_IMAGE_ID} .

# ... or docker-compose
docker-compose -f docker-compose.build.yml build
```

# Contributions
I'm always happy for contributions of any kind. Feel free to post an issue or hit me with a pull request!
