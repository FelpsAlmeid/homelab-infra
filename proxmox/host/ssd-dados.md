# SSD de dados (`ssd-dados`) e migração de containers

SSD SATA dedicado aos containers com banco de dados (Zabbix, NetBox, GLPI), fora do NVMe do sistema.

## Identificar o disco

Os nomes `sdX` **mudam entre boots** (ex.: depois de instalar outro disco). Sempre use `/dev/disk/by-id`:
```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,LABEL,MODEL,SERIAL,TRAN,MOUNTPOINTS
ls -l /dev/disk/by-id/ | grep -v part
```

## Criar o storage (LVM-Thin)

```bash
DISK=/dev/disk/by-id/<ata-MODELO_SERIAL>
wipefs $DISK                       # sem saída = disco vazio (só leitura)
pvcreate $DISK
vgcreate ssd-dados $DISK
lvcreate --type thin-pool -l 95%FREE -n data ssd-dados   # 5% de folga para metadados
pvesm add lvmthin ssd-dados --vgname ssd-dados --thinpool data --content rootdir,images
pvesm status
```

## Migrar um container

```bash
# backup antes (modo stop: discos raw em storage "dir" não têm snapshot)
vzdump <ID> --storage <storage-backup> --mode stop --compress zstd

pct shutdown <ID>
pct move-volume <ID> rootfs ssd-dados    # sem --delete: o disco antigo vira unused0
pct start <ID>
pct config <ID> | grep -E "rootfs|unused"
```
Validar o serviço e só então remover o `unused0` (GUI: *Resources → Unused Disk 0 → Remove*).

## Ordem de boot

Serviços que outros consomem sobem primeiro:
```bash
pct set 105 --onboot 1 --startup order=1          # NetBox (API para o sync)
pct set 106 --onboot 1 --startup order=1          # GLPI (destino dos chamados)
pct set 104 --onboot 1 --startup order=2,up=60    # Zabbix
```
Sem isso, logo após o boot o sync NetBox → Zabbix falha com `No route to host`.

> SSD de entrada (sem DRAM, menor TBW): os ajustes de pouca escrita do PostgreSQL do Zabbix ([`90-zabbix-lowwrite.conf`](../../servicos/zabbix/90-zabbix-lowwrite.conf)) continuam importantes.
