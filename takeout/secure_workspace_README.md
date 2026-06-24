# 🔒 Secure Workspace - Sistema de Segurança para Operações de Arquivo

## Visão Geral

Este módulo implementa **verificações de segurança** para operações de arquivo em IAs assistentes, garantindo:

1. **Fronteiras de Workspace** - Operações ficam restritas ao diretório definido
2. **Detecção de Typos** - Identifica erros comuns de digitação (ex: `sukata` vs `sutaka`)
3. **Proteção de Caminhos** - Bloqueia acesso a diretórios do sistema
4. **Confirmação de Usuário** - Solicita confirmação antes de operações destrutivas
5. **Auditoria** - Log de todas as operações

## Estrutura

```
refatora/
├── .workspace_config.yaml     # Configuração de segurança
├── secure_workspace.py        # Módulo Python de segurança
├── secure_workspace_README.md # Este arquivo
└── .workspace_audit.log      # Log de auditoria (criado automaticamente)
```

## Uso Básico

### Inicialização

```python
from secure_workspace import SecureWorkspace

# Workspace padrão
workspace = SecureWorkspace("/home/sukata/refatora")
```

### Validação de Operações

```python
# Validar uma operação antes de executar
result = workspace.validate_operation("create_file", "/home/sukata/refatora/file.txt")

if result.safe:
    if result.requires_confirmation:
        # Mostrar prompt de confirmação
        prompt = workspace.generate_confirmation_prompt(result)
        print(prompt)
        # Aguardar resposta do usuário...
    else:
        # Executar operação diretamente
        execute_create(result.path)
else:
    # Operações bloqueadas
    print(f"Bloqueado: {result.reason}")
```

### Prompt de Confirmação

```python
# O sistema gera prompts claros:
"""
╔══════════════════════════════════════════════════════════════╗
║ 📄 Criar arquivo?
╠══════════════════════════════════════════════════════════════╣
║
║  📍 Caminho: /home/sukata/refatora/novo_arquivo.txt
║
║  Responda:
║    • 'sim' ou 's' → confirmar
║    • 'não' ou 'n' → cancelar
║    • 'mostrar' ou 'm' → ver conteúdo atual
║
╚══════════════════════════════════════════════════════════════╝

> Sua resposta: _
"""
```

## Verificações de Segurança

### 1. Fronteira de Workspace

```
✅ Permitido: /home/sukata/refatora/projeto/file.txt
❌ Bloqueado: /home/sukata/file.txt (fora do workspace)
❌ Bloqueado: /tmp/file.txt (diretório temporário)
```

### 2. Detecção de Typos

```
❌ DETECTADO: /home/sutaka/project/file.txt
   ↑ Typo! Você quis dizer: /home/sukata/project/file.txt

✅ Correto: /home/sukata/project/file.txt
```

### 3. Caminhos Proibidos

```
❌ /etc/passwd        → Sistema
❌ /var/log          → Sistema
❌ /boot             → Boot
❌ /proc             → Processos
❌ /sys              → Kernel
```

### 4. Operações Destrutivas

```
⚠️ DELETE_FILE      → Requer confirmação
⚠️ DELETE_DIRECTORY → Requer confirmação
⚠️ OVERWRITE_FILE    → Requer confirmação
```

## Integração com Ferramentas

### Como Plugin para Agentes

```python
class SecureFileTool(FileTool):
    """Ferramenta de arquivo com segurança."""
    
    def __init__(self):
        self.workspace = SecureWorkspace("/home/sukata/refatora")
    
    def write(self, path: str, content: str):
        # VALIDAR ANTES DE ESCREVER
        result = self.workspace.validate_operation("create_file", path)
        
        if not result.safe:
            raise PermissionError(result.reason)
        
        if result.requires_confirmation:
            prompt = self.workspace.generate_confirmation_prompt(result)
            response = ask_user(prompt)  # Perguntar ao usuário
            
            if response.lower() in ['n', 'não', 'nao']:
                raise OperationCancelled("Usuário cancelou")
        
        # AGORA executar
        with open(path, 'w') as f:
            f.write(content)
        
        # Log da operação
        self.workspace.log_operation("create_file", path, confirmed=True, success=True)
```

### Como Decorator

```python
from secure_workspace import require_workspace_validation

workspace = SecureWorkspace("/home/sukata/refatora")

@require_workspace_validation(workspace)
def criar_arquivo(path: str, content: str):
    with open(path, 'w') as f:
        f.write(content)
```

## Configuração

Edite `.workspace_config.yaml` para personalizar:

```yaml
workspace:
  root: "/home/sukata/refatora"  # Seu workspace
  allowed_paths:
    - path: "/home/sukata"
      require_confirmation: true

operation_rules:
  always_confirm:
    - action: "delete_file"
      message: "TENÇÃO: Isso excluirá '{path}'. Confirmar?"

typo_detection:
  common_typos:
    - pattern: "sutaka"
      correct: "sukata"
```

## Log de Auditoria

Todas as operações são registradas em `.workspace_audit.log`:

```
2026-04-15T10:42:00 | operation=create_file | path=/home/sukata/refatora/file.txt | user=sukata | confirmed=True | success=True
2026-04-15T10:43:00 | operation=delete_file | path=/home/sukata/refatora/old.txt | user=sukata | confirmed=True | success=True
2026-04-15T10:44:00 | operation=create_file | path=/etc/passwd | user=sukata | confirmed=False | success=False | error=Blocked
```

## Princípios Implementados

### 🔒 Privilégio Mínimo (Least Privilege)

> "Apenas criar onde explicitamente autorizado"

### 🎯 Defesa em Profundidade

Múltiplas camadas de verificação:
1. Fronteira de workspace
2. Caminhos proibidos
3. Detecção de typos
4. Confirmação do usuário

### 📝 Transparência

- Logs claros de todas operações
- Prompts explicativos
- Motivos de bloqueio claros

### ✅ Consentimento Informado

Nunca criar sem perguntar ao usuário quando:
- Operações fora do workspace
- Operações destrutivas
- Arquivos que já existem

## Tests

Execute os testes:

```bash
python3 secure_workspace.py
```

Saída esperada:

```
============================================================
SECURE WORKSPACE - Teste de Validação
============================================================

🔍 Testando: create_file -> /home/sukata/refatora/test.txt
   Safe: True
   Needs confirmation: True

🔍 Testando: create_file -> /home/sutaka/test.txt
   Safe: False
   🚫 Bloqueado: Absolute path outside workspace: /home/sutaka/test.txt

🔍 Testando: create_file -> /etc/passwd
   Safe: False
   🚫 Bloqueado: Absolute path outside workspace: /etc/passwd
```

## Recomendações

1. **Sempre inicialize** o SecureWorkspace no início da sessão
2. **Valide ANTES** de qualquer operação de escrita
3. **Use prompts de confirmação** para operações que precisam de usuário
4. **Revise o log de auditoria** periodicamente
5. **Mantenha o config atualizado** com novos typos comuns

## Licença

MIT License - Uso livre para segurança de IAs assistentes.
