Parlance Coach GGUF weights (parlance-es.gguf, parlance-fr.gguf) go here.

They are gitignored. Produce them with:

  python3.11 training/export_parlance_gguf.py --lang es
  python3.11 training/export_parlance_gguf.py --lang fr

Install-time Play Asset Delivery keeps the base module under Play's size
limit. Debug APKs can also load the same files from
app/src/main/assets/models/.
