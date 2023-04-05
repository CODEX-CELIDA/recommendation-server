# CELIDA Recommendation Server

This is a mock recommendation server for the CELIDA project, serving the latest CELIDA recommendations from github. The only implemented FHIR search parameter is URL for any resource type.

On startup, the server downloads the latest CELIDA recommendations from https://github.com/CODEX-CEDLIA/celida-recommendations and serves them from memory at the FHIR endpoint <base>/fhir.

This recommendation server can be used as input to the [execution engine][EE].

## Usage

1. Clone this repository
2. Build container:

    `docker build -t celida/recommendation-server .`

3. Run container:

    `docker run --env-file celida.env -dp 8000:80 celida/recommendation-server`

4. Query the server:

    `curl http://localhost:8000/<resource-type>?_url=<url>`

    For example:

    `curl http://localhost:8000/fhir/ActivityDefinition?url=https://www.netzwerk-universitaetsmedizin.de/fhir/codex-celida/guideline/covid19-inpatient-therapy/recommended-action/drug-administration-action/no-antithrombotic-prophylaxis-nadroparin-administration-low-weight`


## Contributing

We welcome contributions to this repository! If you have any suggestions or bug reports, please open an issue or a pull request.

## Contact

For more information about the CODEX-CELIDA project, please visit <https://github.com/CODEX-CELIDA>.

[EE]: https://github.com/CODEX-CELIDA/execution-engine
[UI]: https://github.com/CODEX-CELIDA/user-interface
