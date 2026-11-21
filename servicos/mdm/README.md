# VM 112 — mdm (celulares corporativos com Headwind MDM)

Gestão centralizada dos **celulares Android (Samsung)** da empresa com o **Headwind MDM Community** (gratuito, código aberto, self-hosted — os dados ficam em casa). Objetivos: só apps liberados, **hotspot bloqueado**, **sem APK de terceiros** e o usuário não remove o MDM. Em teste com 1 aparelho desde 19/11/2026 (HTTP interno, sem dados reais).

## Arquitetura

| Item | Valor |
|---|---|
| Tipo | **VM** (não LXC): serviço que será exposto e guarda dados pessoais (LGPD) → isolamento de kernel |
| SO | Ubuntu 24.04 LTS (server minimized), OVMF + **Secure Boot** |
| Recursos | 2 vCPU, 4 GB (sem balloon), 32 GB no SSD de dados |
| Rede | VLAN 1010, `10.0.10.13`, firewall do Proxmox ligado |
| Pilha | Nginx `:80` (teste) → Tomcat 10 `127.0.0.1:8080` (Java 21) → PostgreSQL 16 `127.0.0.1:5432` |
| Push | **polling** (MQTT só em `127.0.0.1:31000`, porta 31000 nunca exposta) |
| Versão | Headwind MDM 7.04 (agente 6.40) |

## Firewall do Proxmox

- Entrada **e** saída em `DROP` (padrão da casa)
- Entrada: painel (80) e ping só de `redes-admin`; SSH temporário durante a instalação (sai ao fim — acesso por `qm terminal`)
- Saída: só DNS e NTP; HTTP/HTTPS só em **janela de manutenção** (apt, `certbot renew`)

## Hardening do SO

- IPv6 desligado no GRUB (`ipv6.disable=1` — o `systemd-networkd` reativa IPv6 mesmo com sysctl)
- `sysctl` de rede/kernel endurecido; `unattended-upgrades` só `-security`; `chrony`
- SSH: escuta só no IP da VM, sem root, **só chave**, `AllowUsers`, `MaxAuthTries 3` — arquivo `00-hardening.conf` (no `sshd` vale o **primeiro** valor lido; o `50-cloud-init.conf` reativava senha)
- fail2ban com `backend = systemd` (a imagem minimized não tem `auth.log`)
- Tomcat com `ProtectSystem=strict` + `ReadWritePaths=/var/cache/tomcat10/`; conector só em `127.0.0.1` e `server="-"`
- `ROOT.xml` do Headwind 640 `root:tomcat` (contém segredos — nunca no repositório)

## Parâmetros do Headwind alterados

| Parâmetro | Valor | Motivo |
|---|---|---|
| `secure.enrollment` | `0` | O agente oficial assina com segredo embutido (`signature mismatch` com segredo próprio) e build próprio do agente é barrado pelo Play Protect; usar o segredo público não traz segurança real |
| `hash.secret` | trocado (longo) | o gerado pelo instalador era curto |
| `mqtt.server.uri` | `127.0.0.1:31000` | push por polling |
| `proxy.addresses` | `127.0.0.1` | registrar o IP real do aparelho (`X-Real-IP` do Nginx) |
| `prevent.duplicate.enrollment` | `1` | impede dois aparelhos com o mesmo ID |

**Compensações** por não assinar os métodos REST: painel nunca exposto, Nginx público só com os caminhos do agente, IDs de aparelho difíceis de adivinhar, nenhuma senha de Wi-Fi nas configurações e, como segunda camada, `ui.allowed.address` com as redes administrativas.

## Caminhos usados pelo agente (allowlist da produção)

Só estes ficam públicos; **não liberar `/rest/plugins/` inteiro** (há rotas administrativas nele).

| Caminho | Uso |
|---|---|
| `/files/` | download do agente e APKs |
| `/rest/public/sync/configuration/<ID>` · `/rest/public/sync/info` | configuração e status |
| `/rest/plugins/devicelog/log/list/<ID>` · `/rest/plugins/devicelog/log/rules` | logs do aparelho |
| `/rest/plugins/deviceinfo/deviceinfo/public` · `/rest/plugins/deviceinfo/deviceinfo-plugin-settings/device` | informações do aparelho |

```bash
# refazer o levantamento a partir do log do Nginx
sudo grep -v Mozilla /var/log/nginx/mdm-access.log | awk '{print $7}' | sed -E 's#/[^/]*$##' | sort | uniq -c
```

## Política nos aparelhos

- **Interface original da Samsung (One UI)** com o Headwind em **modo de fundo**, **modo permissivo desligado**: apps não liberados continuam na gaveta, mas pedem a senha do administrador para abrir (testado em 19/11). O lançador gerenciado do Headwind funciona, mas foi descartado por preferência.
- Regra para apps: **app com tela → decidir; serviço de sistema sem tela → Permitir + Ocultar** (bloquear telefonia, teclado ou Permission Controller quebra o aparelho).
- Localização **desligada** (LGPD), USB bloqueado, criptografia e PIN obrigatórios, Wi-Fi fora do QR Code (iria em texto aberto).
- Restrições Android (`UserManager`) aplicadas **uma por vez** e testadas: `no_config_tethering` (aplicada), depois `no_install_unknown_sources_globally`, `no_factory_reset`, `no_safe_boot`, `no_debugging_features`, `no_usb_file_transfer`, `no_add_user`, `no_config_vpn`, `no_config_credentials`, `no_config_date_time`.
- Cadastro: ID de patrimônio (`CNT-CEL-NN`, sem nome de colaborador) → reset de fábrica → 7 toques na tela de boas-vindas → QR Code → patrimônio e termo de uso no GLPI.

## Problemas encontrados

| Sintoma | Causa | Solução |
|---|---|---|
| `UnsupportedClassVersionError` / `NoClassDefFoundError: jakarta/servlet/...` no Ubuntu 22.04 | Headwind 7 usa **Jakarta** (Java 17+) → exige **Tomcat 10**; o Tomcat 9 do 22.04 é `javax` | Reinstalar com **Ubuntu 24.04 + `tomcat10`** (a página do instalador ainda cita 22.04) |
| Headwind não grava arquivos | `ProtectSystem=strict`; `work` aponta para `/var/cache/tomcat10` | `ReadWritePaths` no override + dono `tomcat` |
| Instalador cria conector **8443 com keystore de senha padrão** no `server.xml` (mesmo sem Let's Encrypt) | comportamento do `hmdm_install.sh` | restaurar o `server.xml` do pacote e apagar `/var/lib/tomcat10/ssl` após cada execução do instalador |
| Nginx não sobe: `socket() [::]:80 failed (97)` | site `default` com `listen [::]:80` e IPv6 desligado | remover o site `default` |
| Aparelho: `signature mismatch` | `secure.enrollment=1` com segredo diferente do agente oficial | `secure.enrollment=0` + compensações |

## Pendências

- [ ] Testar as restrições uma a uma no aparelho de teste; conferir Telefone e Configurações no lançador
- [ ] Conta nominal no painel + `admin` desativado + **2FA TOTP**
- [ ] Produção: domínio próprio, certificado, Nginx com a allowlist acima, dst-nat 443 no roteador da DMZ, firewall de produção, HSTS
- [ ] Testar "Novo URL do servidor" para migrar o aparelho de teste sem reset
- [ ] Backup: VM no job diário + dump diário do Postgres + teste de restauração
- [ ] Janela de manutenção semanal (abre/fecha saída, atualizações, renovação do certificado)
- [ ] Zabbix agent 2 + alerta de aparelho sem sincronizar > 24 h; cadastro no NetBox e patrimônio no GLPI
- [ ] Termo de uso (LGPD) e retenção dos logs do aparelho; confirmar o que a Community entrega para aparelho perdido
