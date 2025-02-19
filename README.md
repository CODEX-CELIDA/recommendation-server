# CELIDA Recommendation Server

This is a mock recommendation server for the CELIDA project, serving the latest CELIDA recommendations from github. The only implemented FHIR search parameter is URL for any resource type.

On startup, the server downloads the latest CELIDA recommendations from https://github.com/CODEX-CEDLIA/celida-recommendations and serves them from memory at the FHIR endpoint <base>/fhir.

This recommendation server can be used as input to the [execution engine][EE].

The docker image is available at <https://hub.docker.com/repository/docker/glichtner/celida-recommendation-server/>.

## Usage

### Run locally

1. Copy `celida.env` to `app/.env` and fill in settings.
2. `pip install -r requirements.txt`
3. `cd app`
4. `uvicorn main:app --reload`

### Run with docker

1. Pull image from docker hub

   ```bash
   docker pull glichtner/celida-recommendation-server:latest
   ```

2. Run container with specified environment variables
   ```bash
   docker run \
      -e "GH_REPOSITORY=https://github.com/CODEX-CELIDA/celida-recommendations" \
      --name celida-recommendation-server \
      -dp 8000:80 \
      glichtner/celida-recommendation-server
   ```

### Build image yourself

1. Clone this repository
2. Build image:

   ```bash
    docker build -t celida/recommendation-server .
    ```

3. Run container:

    ```bash
    docker run --env-file celida.env -dp 8000:80 celida/recommendation-server
    ```

## Querying

Get all available versions of the fhir package:

```bash
curl "http://localhost:8000/fhir/version-history"
```

Query the server:

```bash
curl "http://localhost:8000/{fhir-resource-type}?url={url}"
```

For example:

```bash
curl "http://localhost:8000/fhir/PlanDefinition?url=https://www.netzwerk-universitaetsmedizin.de/fhir/codex-celida/guideline/covid19-inpatient-therapy/intervention-plan/peep-fio2-point4"
```


## Contributing

We welcome contributions to this repository! If you have any suggestions or bug reports, please open an issue or a pull request.

## Contact

For more information about the CODEX-CELIDA project, please visit <https://github.com/CODEX-CELIDA>.

[EE]: https://github.com/CODEX-CELIDA/execution-engine
[UI]: https://github.com/CODEX-CELIDA/user-interface
