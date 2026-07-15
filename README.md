# Regulatory Intelligence Assistant (MVP1)

A Streamlit workspace that turns a pasted regulatory / SOP excerpt plus
a product-change scenario into a structured, **source-grounded**
pre-review analysis — risk level, evidence basis, documentation
checklist, follow-up questions, and a human-review disclaimer.

> **This is a pre-review tool, not a final regulatory decision.**
> It only reasons from the text you paste in, and it will say
> "Unclear" rather than guess when the evidence is thin.

## What it does

1. Pick a synthetic sample scenario (or start blank) in the sidebar.
2. Paste regulatory/SOP text and a product-change scenario or question.
3. Click **Analyze Regulatory Impact**.
4. The app calls an LLM via [OpenRouter](https://openrouter.ai), enforces
   a strict "answer only from the pasted text" prompt contract, and
   renders the structured result.
5. Download the result as a Markdown report.

## Project structure

```
regulatory-intelligence-assistant/
  app.py                       # Streamlit entry point
  requirements.txt
  README.md
  .env.example                 # local dev env var template
  .streamlit/
    secrets.toml.example       # deployed secrets template
  src/
    openrouter_client.py       # thin OpenRouter API wrapper
    prompts.py                 # system prompt / analysis contract
    sample_data.py             # 5 synthetic sample scenarios
    ui_helpers.py               # Streamlit rendering helpers
    response_parser.py          # JSON parsing + Markdown export
  tests/
    test_prompt_contract.py
    test_sample_data.py
```

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and add your OPENROUTER_API_KEY (get one at https://openrouter.ai/keys)

streamlit run app.py
```

Open the URL Streamlit prints (usually http://localhost:8501).

## Run the tests

```bash
pip install pytest
pytest tests/ -v
```

## Deploy on Streamlit Community Cloud (fastest option)

1. Push this folder to a GitHub repo (public or private).
2. Go to [share.streamlit.io](https://share.streamlit.io) → **New app**.
3. Point it at your repo, branch `main`, file path `app.py`.
4. Under **Advanced settings → Secrets**, paste:
   ```toml
   OPENROUTER_API_KEY = "sk-or-v1-your-real-key"
   OPENROUTER_MODEL = "openai/gpt-4o-mini"
   ```
5. Click **Deploy**. You'll get a public `*.streamlit.app` URL.

## Deploy on AWS / Azure / a VPS (alternative)

- **AWS**: EC2, App Runner, ECS, or Elastic Beanstalk. Set
  `OPENROUTER_API_KEY` as an environment variable or store it in
  Secrets Manager and inject it at boot.
- **Azure**: App Service or Container Apps. Set `OPENROUTER_API_KEY`
  in App Settings or Key Vault.
- **Hostinger / any VPS**: run Streamlit behind Nginx with systemd or
  Docker, and terminate HTTPS at Nginx. Example systemd unit:
  ```ini
  [Unit]
  Description=Regulatory Intelligence Assistant
  After=network.target

  [Service]
  WorkingDirectory=/opt/regulatory-intelligence-assistant
  Environment="OPENROUTER_API_KEY=sk-or-v1-your-real-key"
  ExecStart=/opt/regulatory-intelligence-assistant/.venv/bin/streamlit run app.py --server.port 8501 --server.address 0.0.0.0
  Restart=always

  [Install]
  WantedBy=multi-user.target
  ```
  Then reverse-proxy `:8501` behind Nginx with a TLS certificate.

> Vercel is **not** recommended for hosting Streamlit directly.

## Data policy

Use **synthetic examples only**. Do not paste real regulated
documents, patient data, confidential SOPs, or customer complaint
data into this app — this is enforced only by policy and UI
reminders, not by technical controls, in MVP1.

## Non-goals for MVP1

- No final regulatory, legal, clinical, or quality approval.
- No PDF OCR, vector database, enterprise authentication, or
  audit-trail storage.
- No automated submission to regulatory authorities or quality
  systems.
- No autonomous classification of reportability, validation status,
  or labeling approval.
