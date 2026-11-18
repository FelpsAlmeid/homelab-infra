# VM 109 — obs-lives (OBS Studio das lives)

VM Windows 11 no host do POP dedicada ao **OBS Studio**: câmeras IP (RTSP) → OBS → **RTMP** para o CDN de TV do provedor. Em produção desde 16/11/2026 (primeira transmissão).

## VM

| Item | Valor |
|---|---|
| Máquina | q35 · OVMF (UEFI, Secure Boot) · TPM 2.0 virtual |
| CPU / RAM | 6 vCPU `host` · 8 GB **sem balloon** (obrigatório com passthrough) |
| Disco | 80 GB `virtio-scsi-single` (`discard`, `iothread`, `ssd`) |
| Rede | VLAN de serviços, IP fixo |
| GPU | RX 580 em passthrough (`hostpci0 …,pcie=1`, vídeo + áudio HDMI) — host: [`proxmox/host/gpu-passthrough-amd.md`](../../proxmox/host/gpu-passthrough-amd.md) |
| Boot | `onboot 1` · `startup order=9,up=60` (sobe depois dos CTs) |

```bash
qm create 109 --name obs-lives --ostype win11 --machine q35 --bios ovmf \
  --efidisk0 local-lvm:1,efitype=4m,pre-enrolled-keys=1 \
  --tpmstate0 local-lvm:1,version=v2.0 \
  --cpu host --sockets 1 --cores 6 --memory 8192 --balloon 0 \
  --scsihw virtio-scsi-single --scsi0 local-lvm:80,discard=on,iothread=1,ssd=1 \
  --net0 virtio,bridge=vmbr0,tag=1010 \
  --ide2 local:iso/Windows11.iso,media=cdrom --ide0 local:iso/virtio-win.iso,media=cdrom \
  --boot order='ide2;scsi0' --vga std --tablet 1 \
  --hostpci0 0000:01:00,pcie=1 \
  --agent enabled=1 --onboot 1 --startup order=9,up=60
```

## Windows

- Instalação com driver `vioscsi` do virtio-win, conta local, `virtio-win-guest-tools` (rede + QEMU Agent), driver AMD **somente driver**, RDP
- Debloat (com snapshot antes): remove apps de consumo e OneDrive, desliga telemetria/Copilot/Recall/Game DVR, Windows Update **manual** e **sem troca de driver**; mantém Defender, Update, Store, Edge/WebView2 e runtimes VC++
- Scripts PowerShell 5.1 **só em ASCII** (UTF-8 sem BOM quebra strings acentuadas)

## OBS

- Saída: RTMP personalizado (servidor e chave fora do repositório) · AMD HW H.264 · CBR 8000 kbps · keyframe 2 s · 1080p30 · AAC 160 kbps
- Cenas: uma por câmera (mídia RTSP com decodificação por hardware) + cena `OVERLAY` aninhada (fonte de navegador com overlay e música; **uma única fonte**, senão a música toca em dobro) · transição stinger
- Arquivos das lives (overlays, músicas, stinger) no compartilhamento `lives` do Samba, com usuário próprio — a VM não enxerga os outros compartilhamentos ([`smb.conf.example`](../samba/smb.conf.example))

## Pendências

- [ ] Testar desligar/ligar a VM sem Código 43 (reset bug)
- [ ] Snapshots pós-configuração e VM 109 no backup diário do host
- [ ] Exportar coleção de cenas e perfil do OBS para o compartilhamento `lives`
- [ ] Rotina de Windows Update fora do horário das lives
- [ ] Monitorar a VM no Zabbix (ICMP + agente) e o RTMP de saída
- [ ] Playlist com músicas comerciais separadas por período do dia (manhã sem remix) — o canal da TV Play é privado (17/11)
- [ ] Pedidos de música por QR Code, só na rede interna: primeiro nome de quem pediu, fila de até 10, 1 pedido por pessoa a cada 10 min, valendo também na tela das câmeras (17/11)
