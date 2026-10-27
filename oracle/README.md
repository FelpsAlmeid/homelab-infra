# Proxy público na Oracle Cloud (ARM, Always Free)

## Rede
- VCN/sub-rede em `10.0.20.0/24` — a faixa padrão `10.0.0.0/16` colidiria com a rede local.
- IP público **reservado** (o efêmero muda e quebra o DNS).

## Firewall em duas camadas
1. **Security List:** 22/tcp (só um IP de origem), 80/tcp, 443/tcp, porta UDP do WireGuard.
2. **iptables da imagem:** as regras precisam entrar **antes** do REJECT:
   ```bash
   sudo iptables -L INPUT -n --line-numbers      # ache a linha do REJECT (N)
   sudo iptables -I INPUT <N> -p tcp --dport 80 -j ACCEPT
   sudo iptables -I INPUT <N> -p tcp --dport 443 -j ACCEPT
   sudo iptables -I INPUT <N> -p udp --dport <PORTA_WG> -j ACCEPT
   sudo netfilter-persistent save
   ```

## Serviços
- [Nginx Proxy Manager](npm/docker-compose.yml) — painel nunca em `0.0.0.0`.
- [WireGuard](wireguard/wg0.conf.example) + [ordem de boot do Docker](docker/after-wg.conf).

## Publicar um serviço novo
1. MikroTik: `accept` para destino/porta **acima** do drop da interface do túnel.
2. Proxmox: regra no CT liberando a porta para `+proxy-oracle`.
3. DNS: registro A do subdomínio → IP da Oracle.
4. NPM: Proxy Host + certificado Let's Encrypt + Force SSL (+ Websockets quando a aplicação usa).
5. Serviço interno (NOC): **Access List** só com os IPs públicos da empresa + bloqueio das APIs — veja [npm/advanced](npm/advanced/README.md). Confira no `.conf` gerado se `allow`/`deny` estão lá.
6. A aplicação precisa de login próprio, cadastro público fechado e MFA.
7. Ajustar a URL pública na aplicação (NetBox: `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS`; GLPI: URL da aplicação; Zabbix: `{$ZABBIX.URL}`) e, no GLPI, liberar o IP do túnel também na `DOCKER-USER`.

Teste do caminho antes do DNS (na Oracle): `curl -sI http://<ip-interno>:<porta>/` → 200.

> Contas Always Free: limites ARM atuais de 2 OCPUs / 12 GB; instâncias ociosas podem ser recuperadas. Conta Pay As You Go + alerta de orçamento evita surpresas.
