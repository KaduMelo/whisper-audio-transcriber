# PRD — Whisper Transcriber

## 1. Objetivo

Criar uma ferramenta CLI em Python capaz de receber um arquivo de áudio e gerar sua transcrição utilizando **Whisper localmente**, sem depender de APIs externas ou serviços pagos.

O foco inicial é transcrever arquivos `.mp3`, mas a implementação deve permitir suporte futuro a outros formatos de áudio e vídeo.

O projeto deve utilizar **uv** para gerenciamento de ambiente e dependências.

---

## 2. Requisitos funcionais

### RF01 — Entrada

O programa deve aceitar o caminho de um arquivo como argumento:

```bash
uv run python transcribe.py audio.mp3
```

### RF02 — Idioma

Deve ser possível informar opcionalmente o idioma:

```bash
uv run python transcribe.py audio.mp3 --language pt
```

Quando não informado, o Whisper deve detectar automaticamente.

### RF03 — Modelo

Deve ser possível escolher o modelo:

```bash
uv run python transcribe.py audio.mp3 --model base
```

Modelos suportados inicialmente:

* `tiny`
* `base`
* `small`
* `medium`
* `large`

O modelo padrão deve ser configurável.

### RF04 — Transcrição

O script deve:

1. Verificar se o arquivo existe.
2. Validar o formato.
3. Carregar o modelo Whisper.
4. Processar o áudio.
5. Gerar a transcrição.
6. Salvar o resultado.

### RF05 — Output

Por padrão, a transcrição deve ser salva em:

```text
output/<nome-do-arquivo>.txt
```

Exemplo:

```text
input/reel.mp3
```

gera:

```text
output/reel.txt
```

### RF06 — Output no terminal

Após finalizar, o programa deve informar:

```text
Transcription completed successfully.
Input: input/reel.mp3
Output: output/reel.txt
Language: pt
Model: base
```

Deve existir uma opção para imprimir a transcrição no terminal:

```bash
uv run python transcribe.py audio.mp3 --print
```

---

# 3. Interface CLI

Uso básico:

```bash
uv run python transcribe.py <file>
```

Opções:

```text
--language
--model
--output
--print
```

Exemplo completo:

```bash
uv run python transcribe.py reel.mp3 \
    --language pt \
    --model small \
    --output ./transcripts \
    --print
```

---

# 4. Estrutura inicial

O MVP deve permanecer simples:

```text
whisper-transcriber/
├── transcribe.py
├── pyproject.toml
├── uv.lock
├── README.md
├── .gitignore
├── input/
└── output/
```

Não criar API, servidor, banco de dados ou arquitetura distribuída no MVP.

Caso a complexidade cresça, o código poderá posteriormente ser separado em módulos.

---

# 5. Gerenciamento de dependências

O projeto deve utilizar **uv**.

**Não utilizar `requirements.txt`.**

Inicialização:

```bash
uv init
```

Adicionar Whisper:

```bash
uv add openai-whisper
```

Executar:

```bash
uv run python transcribe.py audio.mp3
```

O projeto deve versionar o `uv.lock`.

O `pyproject.toml` deve ser a fonte oficial das dependências do projeto.

---

# 6. Dependências

A principal dependência para transcrição deve ser:

```text
openai-whisper
```

Também devem ser incluídas pelo gerenciador as dependências necessárias para execução do Whisper.

O projeto deve documentar a necessidade do **FFmpeg**, necessário para o processamento dos arquivos suportados.

---

# 7. Performance

O modelo Whisper deve ser carregado uma única vez durante a execução do script.

Não deve haver chamadas externas para realizar a transcrição.

A primeira versão deve priorizar simplicidade.

**Não implementar no MVP:**

* filas;
* workers;
* Redis;
* banco de dados;
* Docker;
* FastAPI;
* processamento distribuído.

---

# 8. Tratamento de erros

O programa deve apresentar mensagens claras para:

* arquivo inexistente;
* extensão não suportada;
* arquivo vazio;
* modelo inválido;
* erro durante a transcrição;
* erro ao salvar o resultado.

Exemplo:

```text
Error: Audio file not found: audio.mp3
```

O programa deve retornar exit codes apropriados para permitir automação via shell.

---

# 9. Testes

Criar testes para:

* validação do arquivo;
* geração do nome do output;
* parsing dos argumentos;
* tratamento de arquivos inexistentes;
* serviço de transcrição.

O Whisper deve ser mockado nos testes unitários para evitar processamento real desnecessário.

Os testes devem poder ser executados usando:

```bash
uv run pytest
```

---

# 10. Evolução futura

A arquitetura deve permitir adicionar posteriormente:

* `.mp3`
* `.wav`
* `.m4a`
* `.mp4`
* `.webm`
* timestamps;
* transcrição segmentada;
* detecção de speakers;
* resumo;
* tradução;
* processamento em lote;
* integração com Instagram;
* integração com YouTube;
* interface web;
* API.

**Nenhuma dessas funcionalidades deve ser implementada no MVP.**

---

# 11. Critérios de aceite

O projeto estará concluído quando for possível executar:

```bash
uv run python transcribe.py audio.mp3
```

e obter:

```text
output/audio.txt
```

contendo a transcrição completa do áudio.

Também deve funcionar:

```bash
uv run python transcribe.py audio.mp3 --language pt
```

e:

```bash
uv run python transcribe.py audio.mp3 --model small --print
```

A aplicação deve executar **100% localmente**, sem necessidade de API key ou serviço externo para realizar a transcrição.

---

# 12. Princípios de implementação

O código gerado a partir deste PRD deve seguir:

1. **KISS** — manter o MVP simples.
2. **Clean Code** — código legível e fácil de manter.
3. **Baixo acoplamento** — evitar dependências desnecessárias.
4. **Testabilidade** — código fácil de testar.
5. **Configuration over hardcoding**.
6. **Não implementar funcionalidades futuras prematuramente.**
7. Priorizar execução local.
8. Utilizar `uv` para ambiente e dependências.
9. Não criar API ou frontend no MVP.
10. O script deve ser facilmente executável por linha de comando.

---

# 13. Resultado esperado

Ao final, o usuário deve conseguir colocar um áudio na pasta do projeto e executar:

```bash
uv run python transcribe.py input/reel.mp3 --language pt
```

O sistema deve:

1. Carregar o modelo Whisper.
2. Processar o áudio localmente.
3. Transcrever o conteúdo.
4. Criar automaticamente a pasta `output`, caso ela não exista.
5. Gerar:

```text
output/reel.txt
```

contendo a **transcrição completa e legível do áudio**.

### Exemplo de resultado

Entrada:

```text
input/ReelAudio-82149.mp3
```

Comando:

```bash
uv run python transcribe.py input/ReelAudio-82149.mp3 --language pt
```

Saída:

```text
output/ReelAudio-82149.txt
```

O arquivo `.txt` deve conter somente a transcrição, sem metadados ou informações técnicas desnecessárias.
