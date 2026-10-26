# Driver NVIDIA com Secure Boot ativo

```bash
apt install proxmox-default-headers build-essential dkms
printf 'blacklist nouveau\noptions nouveau modeset=0\n' > /etc/modprobe.d/blacklist-nouveau.conf
update-initramfs -u -k all && reboot

# Chave MOK do DKMS (o DKMS reassina o módulo a cada kernel novo)
dkms generate_mok
mokutil --import /var/lib/dkms/mok.pub      # define uma senha temporária
reboot                                      # tela azul: Enroll MOK -> Continue -> Yes (presencial, uma vez)

mokutil --test-key /var/lib/dkms/mok.pub    # "already enrolled"

./NVIDIA-Linux-x86_64-<versao>.run --dkms \
  --module-signing-secret-key=/var/lib/dkms/mok.key \
  --module-signing-public-key=/var/lib/dkms/mok.pub
# Módulos: MIT/GPL (open) · registrar no DKMS: sim · X config: não

nvidia-smi && mokutil --sb-state && dkms status
```

Depois copie [`nvidia.conf`](nvidia.conf) e [`70-nvidia.rules`](70-nvidia.rules). Antes de reiniciar após um `apt full-upgrade` com kernel novo, confira `dkms status`.
