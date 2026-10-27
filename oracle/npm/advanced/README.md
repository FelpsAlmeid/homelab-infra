# NPM — bloqueio de APIs (aba *Advanced* do Proxy Host)

Os serviços internos publicados no proxy ficam atrás de uma **Access List** (allow só os IPs públicos da empresa; deny all). Além disso, as APIs que só as integrações internas usam são negadas no proxy — as integrações falam direto pela rede interna.

| Serviço | Custom Nginx Configuration | Observação |
|---|---|---|
| Zabbix | `location /api_jsonrpc.php { deny all; }` | O frontend não usa esse endpoint |
| GLPI | `location ~ ^/(apirest\.php\|api\.php) { deny all; }` | Cobre a REST legada e a API nova (`/api.php/v2...`) |
| NetBox | **sem bloqueio** | A interface usa `/api/` pela sessão do navegador (listas de seleção dos formulários). Bloquear quebra criação/edição. Proteção: Access List + tokens v2 com IPs permitidos |

## Conferir o que o NPM gerou

Depois de criar/editar uma Access List, **confira o arquivo do host** — o NPM nem sempre regenera os hosts:

```bash
cd /opt/npm
sudo grep -n -E "allow|deny|satisfy" data/nginx/proxy_host/<N>.conf
```
Precisa haver as linhas `allow ...;` e `deny all;` dentro do `location /`. Só `satisfy all;` sem regras = **acesso liberado para qualquer IP**.

Se faltar: no Proxy Host troque a Access List para *Publicly Accessible* → Save → volte para a lista → Save.

Teste sem depender de outra rede (origem = IP do Docker, fora da lista → esperado **403**):
```bash
curl -sk -o /dev/null -w "%{http_code}\n" --resolve <host>:443:127.0.0.1 https://<host>/
```
