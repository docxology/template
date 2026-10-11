# Zenodo integration

Client for the [Zenodo REST API](https://developers.zenodo.org/) (Deposit: create deposition → upload to bucket → publish → DOI).

```python
from infrastructure.publishing.zenodo import ZenodoClient, ZenodoConfig, publish_to_zenodo

# High-level publish
result = publish_to_zenodo(metadata, [Path("paper.pdf")], access_token="...", sandbox=True)
print(result.doi)

# Step-by-step
client = ZenodoClient(ZenodoConfig(access_token="...", sandbox=True))
dep = client.create_deposition({"title": "My paper", "upload_type": "publication"})
client.upload_file(dep.bucket_url, Path("paper.pdf"))
doi = client.publish(dep.deposition_id)
```

Import clients and workflow helpers from `infrastructure.publishing.zenodo`.
The package root also exports its declared publishing API.

See [AGENTS.md](AGENTS.md) for API details.
