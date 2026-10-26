# Ollama com GPU em LXC

1. No host: driver NVIDIA ([proxmox/host](../../proxmox/host)) e dispositivos no CT ([102-ollama.conf.example](../../proxmox/lxc/102-ollama.conf.example)).
2. No CT, o **mesmo** instalador do host, só userspace:
   ```bash
   ./NVIDIA-Linux-x86_64-<versao>.run --no-kernel-module && nvidia-smi
   ```
3. Ollama (instale o driver **antes**, para o instalador não tentar instalar drivers no LXC):
   ```bash
   apt install -y curl zstd && curl -fsSL https://ollama.com/install.sh | sh
   ```
4. Copie [`override.conf`](override.conf), `systemctl daemon-reload && systemctl restart ollama`.
5. Validação: `ollama ps` deve mostrar `100% GPU`.

Com 12 GB de VRAM: modelos de 7–8B rápidos; 12–14B quantizados ainda cabem inteiros na GPU.
