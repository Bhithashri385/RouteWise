# RouteWise

## Overview
This project demonstrates how to run a local AI model using Ollama and call it from Python.

## Model
- Qwen 2.5 1.5B
- Ollama

## Workflow
Python script → Ollama API → Local Qwen model → Response

## Features
- Sends prompts to a local AI model
- Receives responses through the Ollama API
- Measures response time
- Records generated token counts

## Requirements
- Python 3
- Ollama
- qwen2.5:1.5b
- requests

## How to Run

**1. Download the model**
```bash
ollama pull qwen2.5:1.5b
```

**2. Install the required package**
```bash
python3 -m pip install requests
```

**3. Run the script**
```bash
python3 test_local.py
```

Make sure Ollama is running before executing the script.
