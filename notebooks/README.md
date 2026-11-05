# Notebooks

Google Colab notebooks. API keys were stored in Colab Secrets, so they are not in these notebooks.

| Notebook | What it does | Output |
|---|---|---|
| `DS440_full_run.ipynb` | Full run of Gemini 3.1 Flash-Lite (8,428 prompts, temperature 0), October 27, 2026 | `data/responses/gemini_gemini-3.1-flash-lite.csv` |
| `DS440_SEA_LION_run.ipynb` | Full run of SEA-LION v4.5 27B (8,410 prompts, temperature 0, "thinking" off), October 27–29, 2026, saving every 200 replies to Google Drive | `data/responses/sealion_Qwen-SEA-LION-v4.5-27B-IT.csv` |
| `DS440_analysis_demo.ipynb` | Demo: re-scores the saved replies, checks them against the hand check, runs the analysis and shows the figures; also lets you score your own reply. No API key needed. [Open in Colab](https://colab.research.google.com/github/ammarhafiy/ds440-language-gap/blob/main/notebooks/DS440_analysis_demo.ipynb) | `results/analysis/` |
