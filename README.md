# Whisper Transcriber

CLI em Python que transcreve arquivos de áudio **100% localmente** usando [Whisper](https://github.com/openai/whisper).
Sem API key, sem serviço externo, sem custo por uso.

## Requisitos

- [uv](https://docs.astral.sh/uv/)
- **FFmpeg** — necessário para o Whisper decodificar o áudio:

```bash
# Ubuntu / Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg
```

## Instalação

```bash
uv sync
```

O primeiro uso de cada modelo faz o download dos pesos do Whisper (cacheados em `~/.cache/whisper`).

## Uso

```bash
uv run python transcribe.py input/reel.mp3
```

Gera `output/reel.txt` com a transcrição completa — apenas o texto, sem metadados.

### Opções

| Opção | Padrão | Descrição |
| --- | --- | --- |
| `--language` | detecção automática | Idioma do áudio (ex.: `pt`) |
| `--model` | `base` | Modelo Whisper: `tiny`, `base`, `small`, `medium`, `large` |
| `--output` | `output` | Diretório onde a transcrição é salva (criado se não existir) |
| `--print` | desativado | Imprime a transcrição no terminal |

Exemplo completo:

```bash
uv run python transcribe.py input/reel.mp3 \
    --language pt \
    --model small \
    --output ./transcripts \
    --print
```

Saída no terminal:

```text
Transcription completed successfully.
Input: input/reel.mp3
Output: output/reel.txt
Language: pt
Model: base
```

### Configuração

Os padrões podem ser alterados por variáveis de ambiente, sem editar o código:

| Variável | Padrão | Efeito |
| --- | --- | --- |
| `WHISPER_MODEL` | `base` | Modelo usado quando `--model` não é informado |
| `WHISPER_OUTPUT_DIR` | `output` | Diretório usado quando `--output` não é informado |

```bash
WHISPER_MODEL=small uv run python transcribe.py input/reel.mp3
```

## Formatos suportados

O MVP suporta `.mp3`. Outros formatos (`.wav`, `.m4a`, `.mp4`, `.webm`) podem ser habilitados
adicionando a extensão em `SUPPORTED_EXTENSIONS` (`transcribe.py`).

## Exit codes

Úteis para automação via shell:

| Código | Significado |
| --- | --- |
| `0` | Sucesso |
| `2` | Erro de uso dos argumentos (argparse) |
| `3` | Arquivo não encontrado |
| `4` | Extensão não suportada |
| `5` | Arquivo vazio |
| `6` | Modelo inválido |
| `7` | Falha durante a transcrição |
| `8` | Falha ao salvar o resultado |

## Testes

```bash
uv run pytest
```

O Whisper é mockado nos testes — nenhum modelo é baixado e nenhum áudio é processado de verdade.

## Estrutura

```text
whisper-audio-transcriber/
├── transcribe.py
├── pyproject.toml
├── uv.lock
├── README.md
├── .gitignore
├── input/
├── output/
└── tests/
    └── test_transcribe.py
```
