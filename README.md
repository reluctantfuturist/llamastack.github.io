# Llama Stack Documentation

DONOT MAKE CHANGES TO THIS REPOSITORY DIRECTLY

This repository hosts the GitHub Pages documentation site generated from documentation in [Llama Stack](https://github.com/llamastack/llama-stack).

🔗 **Live Documentation**: https://llamastack.github.io

## Overview

This repository automatically syncs and builds documentation from the main Llama Stack repository using GitHub Actions. The documentation is built using Sphinx and served as static HTML via GitHub Pages.

## Updates

- Manually via GitHub Actions workflow dispatch

## Local Development

To manually build and sync the documentation locally:

```bash
# Clone this repository
git clone https://github.com/llamastack/llamastack.github.io.git
cd llamastack.github.io

# Run the workflow locally (requires Python 3.12 and uv)
./run-workflow.py

# The documentation will be built and copied to the root directory
# You can then serve it locally with any HTTP server, for example:
uv run python -m http.server 8323 --directory docs
```

The `run-workflow.py` script parses and executes the GitHub Actions workflow locally, providing the same build process as the CI/CD pipeline.

## Contributing

Documentation content should be contributed to the main [Llama Stack repository](https://github.com/llamastack/llama-stack/tree/main/docs/source). This repository only hosts the built documentation.

## License

See the [Llama Stack repository](https://github.com/llamastack/llama-stack) for license information.
