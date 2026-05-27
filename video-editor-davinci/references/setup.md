# Setup — video-editor-davinci

Guia one-time para deixar o ambiente pronto. Rode `scripts/check_setup.py` ao final pra confirmar.

## 1. DaVinci Resolve Studio

Confirme que está rodando **Studio**, não free. Studio tem ícone com tarja vermelha "Studio" e o splash inicial mostra o logo.

```bash
ls -la "/Applications/DaVinci Resolve/DaVinci Resolve.app"
```

## 2. Habilitar External Scripting

Resolve tem que ser **iniciado uma vez** para criar os arquivos de config, então:

1. Abra DaVinci Resolve
2. Menu **DaVinci Resolve → Preferences → System → General**
3. Em **External scripting using**, escolha **Local**
4. Save → reinicie o Resolve

Sem isso, qualquer tentativa de conectar via Python falha silenciosamente.

## 3. Variáveis de ambiente

Adicione ao `~/.zshrc`:

```bash
# DaVinci Resolve scripting (Studio only)
export RESOLVE_SCRIPT_API="/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting"
export RESOLVE_SCRIPT_LIB="/Applications/DaVinci Resolve/DaVinci Resolve.app/Contents/Libraries/Fusion/fusionscript.so"
export PYTHONPATH="$PYTHONPATH:$RESOLVE_SCRIPT_API/Modules/"
```

Recarrega: `source ~/.zshrc`

Confirma: `echo $RESOLVE_SCRIPT_API` e `ls "$RESOLVE_SCRIPT_API/Modules/"`

Você deve ver `DaVinciResolveScript.py` lá.

## 4. Homebrew + ffmpeg

```bash
brew install ffmpeg
```

Confirma: `ffmpeg -version | head -1` (deve mostrar versão >=6).

## 5. Python deps

Resolve embute Python 3.10. Para os scripts da skill, usamos o Python 3 do sistema com pacotes de userspace:

```bash
pip3 install --user mlx-whisper jinja2 anthropic
```

Não usamos `pydavinci` (não está no PyPI e tem cobertura incompleta da API). Em vez disso, importamos direto o módulo `DaVinciResolveScript` que vem com o Resolve — é o oficial da Blackmagic.

Notas:
- **mlx-whisper** só funciona em Apple Silicon (M1/M2/M3/M4). Se estiver em Intel, troque por `faster-whisper`.

## 6. (v2) Remotion subprojeto

Pular se MVP. Para overlays custom React-based:

```bash
cd ~/.claude/skills/video-editor-davinci/remotion
npm install
```

## 7. Validação

Com Resolve **aberto**, rode:

```bash
python3 ~/.claude/skills/video-editor-davinci/scripts/check_setup.py
```

Output esperado:

```
✅ DaVinci Resolve Studio: connected (v19.x.x)
✅ Project Manager accessible
✅ ffmpeg: 6.x.x
✅ mlx-whisper: 0.x.x importable
✅ Anthropic SDK: ok
✅ Skill directory layout: ok
```

Se algo falhar, a mensagem indica exatamente o passo a corrigir.

## Troubleshooting

### "Resolve not found" mesmo com env vars certas
- Resolve precisa estar aberto. pydavinci conecta no app rodando.
- External scripting precisa estar "Local" (não "None" ou "Network").
- Reinicie Resolve depois de mudar a preferência.

### "DaVinciResolveScript module not found" no import
- Cheque `echo $PYTHONPATH` — tem que conter o `Modules/` path.
- Se rodando Python via VS Code, abra terminal integrado depois de `source ~/.zshrc` ou configure env vars no settings do VS Code.

### mlx-whisper falha com "Metal not available"
- Você está em Intel Mac → use `pip3 install --user faster-whisper` e ajuste `scripts/transcribe.py` (TODO: alternativa cross-platform).

### Resolve crasha ao executar script externo
- Versão do Resolve nova demais. Pinar versão testada.
- Tente rodar o script Python pelo console interno do Resolve (Workspace → Console) primeiro pra isolar.
