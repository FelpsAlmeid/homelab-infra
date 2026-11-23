# CT 113 — frappe-rh (portal do colaborador)

Portal interno do colaborador com o **Frappe HR**: **escalas** por setor e, nas próximas fases, **solicitações ao RH/DP** (atestados, declarações, trocas de turno, folgas) com triagem antes de lançar no sistema de ponto/folha, que continua sendo o oficial. Piloto com o Suporte N1 + RH/DP desde 20–21/11/2026. Só na rede interna.

## Arquitetura

| Item | Valor |
|---|---|
| Tipo | LXC **não privilegiado** (`nesting=1,keyctl=1`), Debian 13 |
| Recursos | 4 vCPU · 6 GB (8 GB só durante o build) · disco 40 G no SSD de dados |
| Rede | VLAN 1010, `10.0.10.14`, firewall do Proxmox ligado; DNS = controlador de domínio |
| Aplicação | `frappe_docker` com imagem própria (Frappe v16 + ERPNext v16 + HRMS v16) |
| Banco/cache | MariaDB 11.8 + Redis (compose oficial) |
| Publicação | Nginx no CT: 80 → 301; 443 com certificado da **CA interna do AD** → `127.0.0.1:8080` |
| Nome | `rh.<domínio interno>` (registro A no DNS do AD) |

### Build da imagem

- `images/layered/Containerfile` com `apps.json` (`frappe/erpnext` e `frappe/hrms`, branch `version-16`) passado como **secret** (`--secret=id=apps_json,...`), nunca como `--build-arg`.
- O build deixa ~11 GB de cache → `docker builder prune -f` ao final.
- `custom.env` e o `compose.custom.yaml` gerado contêm a senha do banco → `chmod 600`, fora do repositório.
- Porta da aplicação publicada só em `127.0.0.1`; `TRUST_UPSTREAM_FORWARDED_PROTO=on` para o Nginx do CT.

## Firewall do Proxmox

- `policy_in: DROP`, log de entrada ligado durante o piloto
- 443 (e 80 para o redirecionamento) só das redes dos PCs da empresa e da origem de administração; SSH só da administração; ICMP do Zabbix
- ⚠️ Os PCs podem chegar ao CT **depois do NAT** do roteador (origem diferente da rede do PC). Descobrir a origem real pelo log do firewall (`SRC=`) antes de montar os IPSets.

## Login pelo AD e papéis

- **LDAPS** no controlador de domínio (porta 636) com conta de serviço própria (OU de contas de serviço); filtro ignora contas desativadas; e-mail = `userPrincipalName`.
- Papéis vêm dos **grupos padronizados do AD** (por setor/função, nunca por sistema):

| Grupo do AD | Papel no Frappe |
|---|---|
| `SETOR_RH_DP` | HR Manager + HR User |
| `FUNCAO_SUPERVISORES` | Gestor de Setor (papel próprio) |
| `FUNCAO_TI_ADMIN` | System Manager |

- O ERPNext remove o papel *Employee* de usuário sem cadastro de Colaborador vinculado → sempre preencher o `user_id` no Colaborador.
- **MCP** embutido (`/api/v2/mcp`) para o Claude, com usuário técnico e token só no cofre de senhas.

## Escala (Fase 3)

- Departamentos, turnos e lista de feriados da empresa cadastrados; escala migrada da planilha (nov–dez).
- Atribuições que cruzavam o fim do mês foram divididas em duas (uma por mês), para o filtro do mês atual funcionar.

| Quem | Vê | Pode |
|---|---|---|
| Colaborador | só as próprias atribuições do **mês atual** e **aprovadas** | ler |
| Gestor de Setor | escala completa do(s) departamento(s) liberados (User Permission) | criar, editar, enviar ao RH |
| HR User / HR Manager | tudo | aprovar / devolver (Manager também cancela) |

- **Server Script** (Permission Query em Shift Assignment) aplica o filtro do mês atual para quem não é RH, gestor nem administrador.
- **Workflow "Aprovação da Escala":** Rascunho → *Enviar ao RH* (gestor) → Aguardando RH → *Aprovar* → Aprovada pelo RH (docstatus 1) → *Cancelar*; *Devolver ao gestor* volta para Rascunho. A escala só vale depois da aprovação do RH.

## Problemas encontrados

| Sintoma | Causa | Solução |
|---|---|---|
| `bench new-site` falha com *Access denied* | Na v16 é pedido o usuário root do MariaDB | `--db-root-username root --db-root-password ...`; repetir com `--force` após rollback |
| `certutil -ca.cert` → "Muitos argumentos" (PowerShell) | O PowerShell quebra o parâmetro | Usar aspas: `certutil '-ca.cert' arquivo.der` |
| Site com tempo esgotado | Origem real era o IP do NAT, fora dos IPSets | Ler o `SRC=` no log do firewall e ajustar o IPSet |
| "Scheduler is disabled" | Padrão do `new-site` | `bench --site <site> enable-scheduler` |
| Login LDAP "credencial inválida" | Formulário comum | Usar o botão **LDAP/AD** da tela de login |
| "Os scripts do servidor estão desativados" | Flag só no site | `bench set-config -g server_script_enabled 1` + reiniciar |
| Server Script: `module has no attribute 'get_roles'` | Função fora do ambiente protegido | `frappe.db.get_all("Has Role", filters={"parent": user, "parenttype": "User"}, pluck="role")` |

## Pendências

- [ ] Escalas de janeiro a abril e dos demais colaboradores do piloto
- [ ] Fase 4: formulários *Documento RH* (só RH/DP — LGPD) e *Solicitação de Escala*, com workflows
- [ ] Fase 5: regras CLT (interjornada, dias seguidos, limites semanais, cobertura mínima), notificações, **backup** (automático criptografado + vzdump do CT) e teste de restauração
- [ ] Desativar o administrador criado no assistente inicial; reduzir os papéis do usuário do MCP
- [ ] Confirmar a origem (NAT) dos PCs da empresa e ajustar o firewall
- [ ] Cadastrar no NetBox e monitorar no Zabbix (ICMP + 443)
