# Jal-Saathi

A WhatsApp-first farm advisory system (irrigation, pest/disease, fertiliser advice) for Indian farmers, built on AWS.

## Project Structure
- `/cv`: Computer vision pipeline for disease/deficiency/growth-stage classification.
- `/rl`: Water-balance simulator and RL irrigation policy.
- `/backend`: AWS Lambda handlers, the Strands agent, and Step Functions definitions.
- `/infra`: AWS CDK (Python) for infrastructure as code.
- `/web`: Vite + React + TypeScript frontend (farmer dashboard & season replay).
- `/data`: Dataset curation scripts and cached datasets.
- `/docs`: Project documentation.

## Setup Instructions

Ensure you have [uv](https://github.com/astral-sh/uv) and [Node.js](https://nodejs.org/) installed.

Run the setup target to install all dependencies:
```bash
make setup
```

Run tests:
```bash
make test
```
