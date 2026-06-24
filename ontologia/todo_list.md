# 📋 Plano de Ação Atomizado & Lista de Tarefas (Todo List)

Este documento centraliza e atomiza todas as tarefas pendentes, estratégias de mitigação técnica e o plano de escalonamento para a base de conhecimento do Promptcraft.

---

## ⚡ 1. Estratégia de Ingestão e Destilação Gradual (Web & YouTube)
Temos 9.774 URLs de favoritos pendentes para processar. Fazer a varredura em massa imediata causaria bloqueios por IPs (DDoS protection), esgotaria a taxa de requisições de APIs e excederia a cota de tokens.

- [x] **Criar script de processamento em lotes menores**: Desenvolvido e salvo em `ontologia/distilar_incremental.py`. O script processa lotes parametrizáveis (ex: 50 links) com delay amigável (3 segundos).
- [ ] **Configurar Execução Automática (Cron/Cronjob)**:
  - Adicionar no crontab do proot-distro uma tarefa para executar `distilar_incremental.py` 2 vezes ao dia (gerando 100 novas destilações de páginas por dia).
  - *Comando sugerido no crontab*: `0 */12 * * * python3 /home/sukata/promptcraft/ontologia/distilar_incremental.py >> /home/sukata/promptcraft/ontologia/cron_distil.log 2>&1`
- [ ] **Filtro de Densidade de Informação (Lightweight Scraping)**:
  - Otimizar o parser de texto para descartar blocos redundantes de cabeçalho, rodapé e menus laterais de páginas web complexas antes de salvar a destilação no banco, minimizando o tamanho final do banco de dados e tokens armazenados.

---

## 📂 2. Estratégia de Backup via Rclone para a Home `~/`
O upload direto pelo CLI rclone em conexões lentas (< 1MB/s) pode travar ou consumir recursos.

- [ ] **Configuração em Background com Limite de Banda (CLI)**:
  - Se optar por fazer via terminal CLI no Termux, utilize o limitador de banda (`--bwlimit 800k`) e execute sob uma sessão `tmux` desanexada para que o processo rode silenciosamente em background sem afetar a interatividade da rede.
  - *Comando*: `tmux new -d -s rclone_backup "rclone copy ~/ joaonit:Backup_Proot --exclude '.cache/**' --exclude '.npm/**' --exclude '**/__pycache__/**' --bwlimit 800k --progress"`
- [ ] **Configuração via Aplicativo Android (Round Sync / RCX)**:
  - Para permitir Pause & Resume automáticos e uploads apenas quando conectado ao Wi-Fi, use o aplicativo **Round Sync** (disponível no F-Droid/GitHub).
  - **Acesso ao proot-distro pelo app**:
    1. O Termux expõe seus arquivos privados ao Android através do **SAF (Storage Access Framework)**.
    2. No app Round Sync, ao adicionar um repositório local, escolha a opção de navegar usando o provedor de arquivos do sistema.
    3. Selecione a raiz do **Termux** na barra lateral.
    4. Navegue até `usr/var/lib/proot-distro/installed-rootfs/ubuntu/home/sukata` (ou o respectivo caminho da sua imagem proot do Ubuntu).
    5. Configure o agendamento no Round Sync para disparar o backup apenas em Wi-Fi e com o carregador conectado.

---

## 📱 3. Mitigação do Bug de Lag de Tela no Termux (Android UI Redraw)
O travamento de até 1 minuto ao retornar ao app Termux **não é causado pelo Phantom Process Killer** (pois os processos de background da IA continuam rodando e finalizando normalmente enquanto a tela está apagada). O problema é o **gargalo de redesenho do buffer de terminal** que tenta reprocessar milhares de linhas acumuladas na GPU/CPU do celular de uma só vez.

- [ ] **Silenciar Saídas Longas (Redirecionamento de Stdout)**:
  - Nunca execute comandos de sincronização ou compilação longa que imprimam centenas de linhas diretamente na tela ativa do Termux. Redirecione a saída para arquivos de log.
  - *Exemplo*: Substituir `python3 promptcraft.py importar ...` por `python3 promptcraft.py importar ... > sync.log 2>&1 &`.
- [ ] **Uso do TMUX (Terminal Multiplexer)**:
  - Instalar o tmux no proot-distro (`apt install tmux`).
  - Crie uma sessão (`tmux new -s sessao`), execute o comando pesado lá dentro e saia da sessão usando a combinação `Ctrl+b` e depois a tecla `d` (detaching).
  - Dessa forma, o terminal não precisa renderizar nada em tela ativa enquanto você alterna de aplicativo. Ao retornar, você pode rodar `tmux attach -t sessao` apenas para ver o resultado final consolidado.
- [ ] **Diminuir Buffer de Rolagem do Termux**:
  - Pressione e segure na tela do Termux, clique em **More...** -> **Settings** -> **Terminal** -> Mude **Scrollback buffer** para um valor menor (ex: 2000 linhas) para aliviar a memória gráfica de redesenho.

---

## 🗂️ 4. Organização do Banco de Dados por Domínios
Classificação relacional implementada e consolidada no SQLite com as novas tags automáticas geradas:
- [x] **Wikipedia (`domain_wikipedia`)**: 2.164 nós mapeados.
- [x] **Buscas (`domain_buscas`)**: 3.843 consultas Google/Bing estruturadas.
- [x] **Youtube (`domain_youtube`)**: 4.355 canais e vídeos indexados.
- [x] **Artigos Científicos (`domain_artigos_cientificos`)**: 525 artigos de pesquisa (arXiv e Semantic Scholar).
- [x] **Sites Autenticados (`domain_sites_autenticados`)**: 850 links de GDrive, Notion, Slack e GitHub Settings.
- [x] **Fontes Dinâmicas (`domain_fontes_dinamicas`)**: 50 plataformas de gráficos de mercado e dashboards (TradingView, Dune, DeFiLlama).

---

## 🚀 5. Próximos Passos de Integração e Desenvolvimento
- [ ] **Script de Bootstrap Emacs-Denote (`pkm-bootstrap.el`)**:
  - Escrever arquivo de inicialização elisp que lê os nós do `fontes_processadas.db` filtrando por tags de domínio e gerando notas `.org` correspondentes no Denote do Emacs.
- [ ] **Geração de Chunks de LoRA para Fine-Tuning**:
  - Compilar as 227 fontes já processadas e destiladas com os chatlogs em um dataset formato JSONL Alpaca para rodar treinamento de compressão semântica via Unsloth.
