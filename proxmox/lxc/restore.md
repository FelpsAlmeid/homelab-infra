# Restaurar containers de um servidor antigo como não privilegiados

```bash
pct restore <NOVO_ID> /caminho/vzdump-lxc-<ID>-<data>.tar.zst \
  --storage local-lvm --unique 1 --unprivileged 1 --ignore-unpack-errors 1

sed -i '/^lxc\./d' /etc/pve/lxc/<NOVO_ID>.conf          # remove permissões extras herdadas
pct set <NOVO_ID> -features nesting=1,keyctl=1            # Docker
pct set <NOVO_ID> -net0 name=eth0,bridge=vmbr0,firewall=1,ip=<IP>/24,gw=<GW>,tag=<VLAN>,type=veth
```

- `--unique 1`: MAC novo.
- `--ignore-unpack-errors 1`: ignora arquivos de dispositivo (`mknod`) que um CT não privilegiado não pode criar; são recriados pelos serviços.
- Use um ID novo se o original já estiver em uso — restaurar no mesmo ID sobrescreve o container existente.
- Depois: revisar firewall interno, `ALLOWED_HOSTS`/URLs da aplicação e caches com datas erradas.
