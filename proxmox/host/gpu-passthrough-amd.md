# Passthrough de GPU AMD (RX 580) para VM — host do POP

Host com Intel i7-10700 (vídeo integrado fica para o console do host) e RX 580 dedicada à VM do OBS.

```bash
# Kernel: IOMMU (GRUB, root em LVM)
cp /etc/default/grub /root/grub.bak-$(date +%F)
sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on iommu=pt"/' /etc/default/grub
update-grub

# Módulos VFIO
printf 'vfio\nvfio_iommu_type1\nvfio_pci\n' > /etc/modules-load.d/vfio.conf

# Reservar a placa (vídeo + áudio HDMI) para o vfio-pci antes do amdgpu/radeon
cat > /etc/modprobe.d/vfio.conf <<'CONF'
options vfio-pci ids=1002:67df,1002:aaf0 disable_vga=1
softdep amdgpu pre: vfio-pci
softdep radeon pre: vfio-pci
CONF

update-initramfs -u -k all && reboot
```

Validação: `dmesg | grep -e DMAR -e IOMMU` (IOMMU enabled + IRQ remapping), `lspci -nnk -d 1002:` com `Kernel driver in use: vfio-pci` e a placa sozinha no seu grupo IOMMU.

> **Reset bug das Polaris:** ao iniciar a VM aparece `failed to reset PCI device` — esperado (a RX 580 não aceita FLR). Se a placa voltar travada depois de desligar/ligar a VM (tela preta, Código 43): módulo `vendor-reset` no host ou reiniciar o host.
