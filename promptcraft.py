#!/usr/bin/env python3
import os
import sys
import re
import json
import csv
import argparse
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime
from html.parser import HTMLParser

# Setup base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
ONTOLOGIA_DIR = os.path.join(BASE_DIR, 'ontologia')
SESSOES_DIR = os.path.join(BASE_DIR, 'sessoes')
BACKUPS_DIR = os.path.join(BASE_DIR, 'backups')

# Volatility configuration as per Section 10 ①
VOLATILITY_SCORES = {
    "video": 5,        # Stream audiovisual (Média)
    "document": 2,     # Documentos estáticos (Baixa)
    "code": 8,         # Repositórios de código (Alta)
    "feed": 9,         # Feeds e comunidades (Alta)
    "data": 10,        # Dados quantitativos (Muito alta)
    "personal": 6,     # Arquivos pessoais (Variável)
    "bookmark": 4      # Favoritos/bookmarks (Média)
}

# ANSI Colors for beautiful outputs
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def log_info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {msg}")

def log_success(msg):
    print(f"{Colors.GREEN}[✓] {msg}{Colors.ENDC}")

def log_warning(msg):
    print(f"{Colors.WARNING}[⚠️ WARNING]{Colors.ENDC} {msg}")

def log_error(msg):
    print(f"{Colors.FAIL}[✗] Erro: {msg}{Colors.ENDC}", file=sys.stderr)

# HTML Parsing to extract plain text without external dependencies
class HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ignore_stack = []
        self.text_parts = []
        self.ignore_tags = {'script', 'style', 'header', 'footer', 'nav', 'iframe', 'noscript'}
        self.current_href = None
        self.has_body = False
        self.in_body = False

    def handle_starttag(self, tag, attrs):
        t_lower = tag.lower()
        if t_lower == 'body':
            self.has_body = True
            self.in_body = True
            self.text_parts = []  # Descarta metadados/títulos do head caso exista tag body
        elif t_lower in self.ignore_tags:
            self.ignore_stack.append(t_lower)
        elif t_lower == 'a':
            for name, value in attrs:
                if name == 'href':
                    self.current_href = value
                    break

    def handle_endtag(self, tag):
        t_lower = tag.lower()
        if t_lower == 'body':
            self.in_body = False
        elif t_lower in self.ignore_tags:
            if t_lower in self.ignore_stack:
                self.ignore_stack.remove(t_lower)
        elif t_lower == 'a':
            self.current_href = None

    def handle_data(self, data):
        # Grava apenas se não estivermos dentro de tags ignoradas e estivermos no body (ou o doc não possui tag body)
        if not self.ignore_stack and (self.in_body or not self.has_body):
            cleaned = data.strip()
            if cleaned:
                if self.current_href and self.current_href.strip() and not self.current_href.lower().startswith('javascript:'):
                    self.text_parts.append(f"[{cleaned}]({self.current_href.strip()})")
                else:
                    self.text_parts.append(cleaned)

    def get_text(self):
        return "\n".join(self.text_parts)

def fetch_url_text(url):
    log_info(f"Buscando conteúdo da URL: {url} ...")
    
    # Check if this is a YouTube video URL
    video_id = None
    if "youtube.com" in url.lower() or "youtu.be" in url.lower():
        if "youtu.be" in url.lower():
            video_id = url.split('/')[-1].split('?')[0]
        else:
            import urllib.parse
            parsed = urllib.parse.urlparse(url)
            queries = urllib.parse.parse_qs(parsed.query)
            if "v" in queries:
                video_id = queries["v"][0]
                
    if video_id:
        log_info(f"Detectado vídeo do YouTube. Tentando extrair transcrição para o ID: {video_id} ...")
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=['pt', 'en', 'es'])
            transcript_text = " ".join([t.text for t in transcript_list])
            return f"YouTube Video Transcript (ID: {video_id}):\n\n{transcript_text}"
        except Exception as e:
            log_warning(f"Não foi possível obter a transcrição do YouTube via API ({e}). Usando fallback estático...")

    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
        parser = HTMLTextExtractor()
        parser.feed(html)
        text = parser.get_text()
        text = re.sub(r'\n+', '\n', text)
        return text
    except Exception as e:
        raise Exception(f"Erro ao obter URL: {e}")

# .env and config loader
def load_config():
    config_path = os.path.join(BASE_DIR, 'config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def get_volatility_score(source_type):
    config = load_config()
    vol_config = config.get("volatility", {})
    vol_label = vol_config.get(source_type.lower())
    
    vol_mapping = {
        "baixo": 2,
        "medio": 5,
        "alto": 8,
        "muito-alto": 10
    }
    if vol_label and vol_label.lower() in vol_mapping:
        return vol_mapping[vol_label.lower()]
        
    default_scores = {
        "video": 5,
        "document": 2,
        "code": 8,
        "feed": 9,
        "data": 10,
        "personal": 6,
        "bookmark": 4
    }
    return default_scores.get(source_type.lower(), 5)

def load_env(filepath):
    if not os.path.exists(filepath):
        return {}
    env_vars = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                key, val = line.split('=', 1)
                env_vars[key.strip()] = val.strip().strip('"').strip("'")
    return env_vars

# API Key resolution
def resolve_api_key(provider, cli_key=None):
    if cli_key:
        return cli_key
        
    env_vars = {}
    for env_path in [os.path.join(os.getcwd(), '.env'), os.path.join(BASE_DIR, '.env')]:
        if os.path.exists(env_path):
            env_vars.update(load_env(env_path))
            
    config_vars = load_config()

    key_env_names = {
        "openai": ["OPENAI_API_KEY"],
        "anthropic": ["ANTHROPIC_API_KEY"],
        "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "huggingface": ["HF_API_KEY", "HF_TOKEN"]
    }

    names = key_env_names.get(provider, [])
    
    # 1. Check environment variables
    for name in names:
        if name in os.environ:
            return os.environ[name]
            
    # 2. Check loaded .env variables
    for name in names:
        if name in env_vars:
            return env_vars[name]
            
    # 3. Check config.json keys
    config_key_names = {
        "openai": "openai_api_key",
        "anthropic": "anthropic_api_key",
        "gemini": "gemini_api_key",
        "huggingface": "huggingface_api_key"
    }
    config_name = config_key_names.get(provider)
    if config_name and config_name in config_vars:
        return config_vars[config_name]
        
    return None

def resolve_all_api_keys(provider, cli_key=None):
    """
    Resolves all configured API keys for a provider.
    Returns a list of strings (keys).
    """
    if provider in ["agent", "antigravity"]:
        return ["agent_key"]
        
    if cli_key:
        return [cli_key]
        
    keys = []
    
    # Standard env variable names for this provider
    key_env_names = {
        "openai": ["OPENAI_API_KEY"],
        "anthropic": ["ANTHROPIC_API_KEY"],
        "gemini": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "huggingface": ["HF_API_KEY", "HF_TOKEN"]
    }
    names = key_env_names.get(provider, [])
    
    # Load .env variables
    env_vars = {}
    for env_path in [os.path.join(os.getcwd(), '.env'), os.path.join(BASE_DIR, '.env')]:
        if os.path.exists(env_path):
            env_vars.update(load_env(env_path))
            
    # Load config.json
    config_vars = load_config()
    
    # Helper to clean and add key
    def add_key(val):
        if not val:
            return
        if isinstance(val, list):
            for v in val:
                if v and v not in keys:
                    keys.append(v)
        elif isinstance(val, str):
            # Support comma-separated keys
            for part in val.split(','):
                part = part.strip()
                if part and part not in keys:
                    keys.append(part)

    # 1. Check environment variables (both standard and suffixed like _1, _2, _3)
    for name in names:
        # Check standard name
        if name in os.environ:
            add_key(os.environ[name])
        # Check suffixed names in os.environ
        for i in range(1, 10):
            suffixed = f"{name}_{i}"
            if suffixed in os.environ:
                add_key(os.environ[suffixed])
                
    # 2. Check loaded .env variables (both standard and suffixed)
    for name in names:
        if name in env_vars:
            add_key(env_vars[name])
        for i in range(1, 10):
            suffixed = f"{name}_{i}"
            if suffixed in env_vars:
                add_key(env_vars[suffixed])
                
    # 3. Check config.json keys
    config_key_names = {
        "openai": "openai_api_key",
        "anthropic": "anthropic_api_key",
        "gemini": "gemini_api_key",
        "huggingface": "huggingface_api_key"
    }
    config_name = config_key_names.get(provider)
    if config_name:
        # Check standard config key
        if config_name in config_vars:
            add_key(config_vars[config_name])
        # Check config backup keys (either a list or config_name_1, etc.)
        backup_name = f"{config_name}_backup"
        if backup_name in config_vars:
            add_key(config_vars[backup_name])
        for i in range(1, 10):
            suffixed = f"{config_name}_{i}"
            if suffixed in config_vars:
                add_key(config_vars[suffixed])
                
    return keys

def autodetect_provider_and_model():
    providers_to_check = ["openai", "anthropic", "gemini", "huggingface"]
    for prov in providers_to_check:
        key = resolve_api_key(prov)
        if key:
            if prov == "openai":
                return "openai", "gpt-4o-mini", key
            elif prov == "anthropic":
                return "anthropic", "claude-3-5-sonnet-20240620", key
            elif prov == "gemini":
                return "gemini", "gemini-1.5-flash", key
            elif prov == "huggingface":
                return "huggingface", "meta-llama/Llama-3.3-70B-Instruct", key
    # Fallback to agent provider if no keys are found
    return "agent", "self", "agent_key"

def get_generator(provider, model_name, api_key, temperature):
    if provider == "openai":
        try:
            from openai import OpenAI
        except ImportError:
            log_error("O pacote 'openai' não está instalado. Instale-o com: pip install openai")
            sys.exit(1)
        client = OpenAI(api_key=api_key)
        def generate(prompt):
            res = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            return res.choices[0].message.content
        return generate

    elif provider == "anthropic":
        try:
            from anthropic import Anthropic
        except ImportError:
            log_error("O pacote 'anthropic' não está instalado. Instale-o com: pip install anthropic")
            sys.exit(1)
        client = Anthropic(api_key=api_key)
        def generate(prompt):
            res = client.messages.create(
                model=model_name,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature
            )
            return res.content[0].text
        return generate

    elif provider == "gemini":
        try:
            import google.generativeai as genai
        except ImportError:
            log_error("O pacote 'google-generativeai' não está instalado. Instale-o com: pip install google-generativeai")
            sys.exit(1)
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        def generate(prompt):
            res = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=temperature)
            )
            return res.text
        return generate

    elif provider == "huggingface":
        def generate(prompt):
            url = "https://router.huggingface.co/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 promptcraft-cli"
            }
            payload = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature
            }
            try:
                import json
                data = json.dumps(payload).encode('utf-8')
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=60) as response:
                    res_json = json.loads(response.read().decode('utf-8'))
                    return res_json['choices'][0]['message']['content']
            except Exception as e:
                if hasattr(e, 'read'):
                    error_details = e.read().decode('utf-8')
                    raise Exception(f"Erro na API Hugging Face: {e}. Detalhes: {error_details}")
                raise Exception(f"Erro na API Hugging Face: {e}")
        return generate
    elif provider in ["agent", "antigravity"]:
        def generate(prompt):
            print("\n=== AGENT_PROMPT_START ===")
            print(prompt)
            print("=== AGENT_PROMPT_END ===")
            print("\n[Aguardando resposta do agente Antigravity. Insira a resposta e finalize com a linha '=== AGENT_RESPONSE_END ===']")
            sys.stdout.flush()
            lines = []
            while True:
                try:
                    line = sys.stdin.readline()
                    if not line:
                        break
                    if line.strip() == "=== AGENT_RESPONSE_END ===":
                        break
                    lines.append(line)
                except KeyboardInterrupt:
                    break
            return "".join(lines).strip()
        return generate
    else:
        log_error(f"Provedor desconhecido '{provider}'")
        sys.exit(1)

# Helper to substitute template variables without using .format()
def substitute_template(template_content, variables):
    result = template_content
    for key, val in variables.items():
        placeholder = "{" + key + "}"
        result = result.replace(placeholder, str(val))
    return result

def load_template_file(template_name, variables):
    # Determine base clean name
    base_name = template_name[:-3] if template_name.endswith(".md") else template_name
    base_clean = base_name.split("__v")[0]
    
    if not os.path.exists(TEMPLATES_DIR):
        raise FileNotFoundError(f"Diretório de templates não encontrado: {TEMPLATES_DIR}")
        
    files = os.listdir(TEMPLATES_DIR)
    best_file = None
    best_major = -1
    best_minor = -1
    
    for f in files:
        if not f.endswith(".md"):
            continue
        f_base = f[:-3]
        f_clean = f_base.split("__v")[0]
        
        if f_clean == base_clean:
            major, minor = 0, 0
            if "__v" in f_base:
                ver_part = f_base.split("__v")[1]
                match = re.match(r'^(\d+)\.(\d+)$', ver_part)
                if match:
                    major = int(match.group(1))
                    minor = int(match.group(2))
            
            if major > best_major or (major == best_major and minor > best_minor):
                best_major = major
                best_minor = minor
                best_file = f
                
    if not best_file:
        fallback_path = os.path.join(TEMPLATES_DIR, template_name)
        if os.path.exists(fallback_path):
            best_file = template_name
        else:
            raise FileNotFoundError(f"Nenhum template encontrado correspondente a '{template_name}'")
            
    template_path = os.path.join(TEMPLATES_DIR, best_file)
    log_info(f"Carregando template: {best_file}")
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return substitute_template(content, variables)

def create_backup(filepath):
    if not os.path.exists(filepath):
        return
    if not os.path.exists(BACKUPS_DIR):
        os.makedirs(BACKUPS_DIR)
    filename = os.path.basename(filepath)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUPS_DIR, f"{filename}.{timestamp}.bak")
    with open(filepath, 'r', encoding='utf-8') as src:
        content = src.read()
    with open(backup_path, 'w', encoding='utf-8') as dest:
        dest.write(content)
    log_info(f"Backup de {filename} salvo em {backup_path}")

# CLI Commands
def cmd_init(args):
    """Initializes the promptcraft directories and default templates/files if they do not exist."""
    log_info("Inicializando repositório promptcraft...")
    for path in [TEMPLATES_DIR, ONTOLOGIA_DIR, SESSOES_DIR, BACKUPS_DIR]:
        if not os.path.exists(path):
            os.makedirs(path)
            log_success(f"Diretório criado: {path}")

    # Write config.json template if it doesn't exist
    config_path = os.path.join(BASE_DIR, 'config.json')
    if not os.path.exists(config_path):
        config_data = {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "openai_api_key": "",
            "anthropic_api_key": "",
            "gemini_api_key": "",
            "temperature": 0.2,
            "volatility": {
                "video": "medio",
                "document": "baixo",
                "code": "alto",
                "feed": "alto",
                "data": "muito-alto",
                "personal": "medio",
                "bookmark": "medio"
            }
        }
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)
        log_success(f"Arquivo de configuração padrão criado: {config_path}")

    log_success("Inicialização completa! Certifique-se de que os templates estão corretos no diretório templates/.")

def cmd_triar(args):
    """Runs only the P1-P3 triage process on the source input."""
    # Resolve content
    content = get_input_content(args)
    if not content:
        log_error("Nenhum conteúdo de entrada fornecido. Use --text, --file ou --url.")
        sys.exit(1)

    generate = get_generator_with_fallback(args)
    provider = getattr(generate, 'last_provider', 'unknown')
    model = getattr(generate, 'last_model', 'unknown')

    # Read existing principles (resumo base existente)
    canonicos_path = os.path.join(ONTOLOGIA_DIR, 'principios_canonicos.md')
    resumo_base = ""
    if os.path.exists(canonicos_path):
        with open(canonicos_path, 'r', encoding='utf-8') as f:
            resumo_base = f.read()

    # If base has only header or is short, log warning
    if not resumo_base.strip() or len(resumo_base.strip()) < 100:
        log_warning("A base de princípios canônicos está vazia ou muito curta. Triagem pode ser menos precisa.")

    log_info(f"Iniciando triagem usando {provider} ({model})...")
    triagem_prompt = load_template_file('triagem_continua.md', {
        "RESUMO_BASE_EXISTENTE": resumo_base,
        "CONTEUDO": content
    })

    result = generate(triagem_prompt)
    provider = getattr(generate, 'last_provider', provider)
    model = getattr(generate, 'last_model', model)
    print(f"\n{Colors.BOLD}=== RESULTADO DA TRIAGEM ==={Colors.ENDC}")
    print(result.strip())
    print("============================\n")

    classification = extract_classification(result)
    if classification:
        log_info(f"Classificação detectada: {classification}")
    else:
        log_warning("Não foi possível extrair a classificação final entre colchetes.")

def cmd_processar(args):
    r"""
    Executes the complete pipeline (Triagem, Etapa 1, Etapa 2, Etapa 3, and updates ontology).
    
    Formalismo Simbólico (Seção 11):
      f_i ∈ F  →  Φ(f_i)  →  a_i
      A' = R(A ⊕ a_i)
      L' = L ∪ lacunas(a_i) \ respostas(a_i)
      Invariante: |A_k| cresce sublinearmente enquanto cobertura_semântica(A_k) cresce linearmente.
    """
    # 1. Resolve content
    content = get_input_content(args)
    if not content:
        log_error("Nenhum conteúdo de entrada fornecido. Use --text, --file ou --url.")
        sys.exit(1)

    generate = get_generator_with_fallback(args)

    # Pre-distill large contents (Point 4 of scaling plan)
    content = summarize_large_content(content, generate)

    # Resolve source metadata
    source_type = args.source_type
    source_ref = args.source_ref
    domain = args.domain

    # Determine volatility score (Section 10 ① / Metacriticism ③)
    volatility = get_volatility_score(source_type)

    # 2. Triagem (P1-P3 Filter)
    canonicos_path = os.path.join(ONTOLOGIA_DIR, 'principios_canonicos.md')
    resumo_base = ""
    if os.path.exists(canonicos_path):
        with open(canonicos_path, 'r', encoding='utf-8') as f:
            resumo_base = f.read()

    classification = "[NÓ-NOVO-DE-CONHECIMENTO]" # Default if forced
    if not args.force:
        log_info("Etapa 0: Executando Triagem Contínua...")
        triagem_prompt = load_template_file('triagem_continua.md', {
            "RESUMO_BASE_EXISTENTE": resumo_base,
            "CONTEUDO": content
        })
        triagem_result = generate(triagem_prompt)
        classification = extract_classification(triagem_result)
        
        log_info(f"Resultado da Triagem: {triagem_result.strip()}")
        
        if classification in ["[RUÍDO-DE-BAIXA-DENSIDADE]", "[REDUNDANTE-CONFIRMATIVO]"]:
            log_warning(f"A fonte foi rejeitada pela triagem como: {classification}")
            log_warning("Use a opção --force para ignorar a triagem e processar assim mesmo.")
            sys.exit(0)
    else:
        log_info("Triagem ignorada (--force ativado).")

    # Metacognition suffix block (Section 8)
    metacog = f"\n\n[INSTRUÇÃO INTERNA PARA O MODELO]\nAntes de entregar a resposta final, audite seu próprio raciocínio:\n  ✓ Há inferência não suportada pelo conteúdo da fonte?\n  ✓ Há viés de confirmação com o domínio {domain}?\n  ✓ A síntese é transferível para um domínio diferente?\nSe qualquer resposta for incerta → marcar o trecho com [⚠️ INCERTEZA] antes de prosseguir\n"

    # 3. Etapa 1 — Desconstrutor Atômico
    log_info("Etapa 1: Executando Desconstrutor Atômico...")
    etapa1_prompt = load_template_file('desconstrutor_atomico.md', {
        "TIPO": source_type,
        "REFERENCIA": source_ref,
        "DOMINIO": domain,
        "CONTEUDO": content
    }) + metacog
    etapa1_output = generate(etapa1_prompt)
    print(f"\n{Colors.GREEN}=== OUTPUT ETAPA 1 (Desconstrutor) ==={Colors.ENDC}")
    print(etapa1_output.strip())

    # 4. Etapa 2 — Tecelão Nexialista
    log_info("Etapa 2: Executando Tecelão Nexialista...")
    etapa2_prompt = load_template_file('tecelao_nexialista.md', {
        "ETAPA1_OUTPUT": etapa1_output
    }) + metacog
    etapa2_output = generate(etapa2_prompt)
    print(f"\n{Colors.GREEN}=== OUTPUT ETAPA 2 (Tecelão) ==={Colors.ENDC}")
    print(etapa2_output.strip())

    # 5. Etapa 3 — Refatorador Ontológico
    log_info("Etapa 3: Executando Refatorador Ontológico...")
    # Section 10 ② check: ensure existing base is present
    if not resumo_base or len(resumo_base.strip()) < 50:
        log_warning("A base existente é muito curta ou vazia. A Etapa 3 prosseguirá, mas lembre-se de que necessita de uma base real para melhor performance.")

    etapa3_prompt = load_template_file('refatorador_ontologico.md', {
        "ETAPA2_OUTPUT": etapa2_output,
        "RESUMO_BASE_EXISTENTE": resumo_base
    }) + metacog
    etapa3_output = generate(etapa3_prompt)
    print(f"\n{Colors.GREEN}=== OUTPUT ETAPA 3 (Refatorador - Diff Semântico) ==={Colors.ENDC}")
    print(etapa3_output.strip())

    # 6. Apply semantic diff to principios_canonicos.md
    log_info("Integrando alterações na base canônica aplicando o diff semântico...")
    apply_prompt = load_template_file('aplicar_diff_semantico.md', {
        "PRINCIPIOS_CANONICOS": resumo_base,
        "DIFF_SEMANTICO": etapa3_output
    })
    new_canonicos = generate(apply_prompt)
    
    # Assert Seção 11 Invariante: A' = R(A ⊕ a_i)
    assert len(new_canonicos.strip()) > 0, "Erro Invariante: A nova base canônica (A') está vazia."
    if len(resumo_base.strip()) > 100:
        assert len(new_canonicos.strip()) >= 0.7 * len(resumo_base.strip()), "Erro Invariante: A base canônica (A') sofreu compressão catastrófica (>30% de perda)."

    # Save base backup and write updated base
    create_backup(canonicos_path)
    with open(canonicos_path, 'w', encoding='utf-8') as f:
        f.write(new_canonicos.strip() + "\n")
    log_success("Base viva de princípios canônicos atualizada com sucesso!")

    # Save Stage 3 Semantic Diff to log_refatoracoes.md (Point ⑥)
    log_path = os.path.join(ONTOLOGIA_DIR, 'log_refatoracoes.md')
    create_backup(log_path)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"\n## Processamento de Fonte ({source_type}) - {timestamp}\n")
        f.write(f"- **Referência**: {source_ref}\n")
        f.write(f"- **Domínio**: {domain}\n\n")
        f.write(f"### Diff Semântico (Etapa 3)\n")
        f.write(etapa3_output.strip() + "\n")
        f.write("\n---\n")
    log_success("Diff semântico registrado no log de refatorações.")

    # 7. Update lacunas_abertas.md
    lacunas_path = os.path.join(ONTOLOGIA_DIR, 'lacunas_abertas.md')
    current_lacunas = ""
    if os.path.exists(lacunas_path):
        with open(lacunas_path, 'r', encoding='utf-8') as f:
            current_lacunas = f.read()

    log_info("Atualizando lacunas abertas com base no diff da Etapa 3...")
    lacunas_update_prompt = f"""
    Aqui está o arquivo de lacunas abertas atual (`lacunas_abertas.md`):
    ---
    {current_lacunas}
    ---
    
    E o output da Etapa 3 contendo novas lacunas ou resoluções:
    ---
    {etapa3_output}
    ---
    
    [TAREFA]
    Atualize o arquivo de lacunas abertas. Remova qualquer pergunta que foi respondida ou tratada no diff, e adicione as novas perguntas/lacunas levantadas.
    Retorne APENAS o novo conteúdo Markdown completo do arquivo `lacunas_abertas.md`. Não adicione explicações, preambles ou comentários fora do markdown resultante.
    """
    new_lacunas = generate(lacunas_update_prompt)
    
    # Assert Seção 11 Invariante: L' = L ∪ lacunas(a_i) \ respostas(a_i)
    assert len(new_lacunas.strip()) > 0, "Erro Invariante: O novo arquivo de lacunas (L') está vazio."

    create_backup(lacunas_path)
    with open(lacunas_path, 'w', encoding='utf-8') as f:
        f.write(new_lacunas.strip() + "\n")
    log_success("Arquivo de lacunas abertas atualizado com sucesso!")

    # 8. Save session file
    date_str = datetime.now().strftime("%Y-%m-%d")
    sanitized_domain = re.sub(r'[^a-zA-Z0-9_-]', '_', domain.lower())
    session_filename = f"{date_str}_{sanitized_domain}.md"
    session_filepath = os.path.join(SESSOES_DIR, session_filename)

    # Ensure unique file name if it already exists
    counter = 1
    while os.path.exists(session_filepath):
        session_filename = f"{date_str}_{sanitized_domain}_{counter}.md"
        session_filepath = os.path.join(SESSOES_DIR, session_filename)
        counter += 1

    session_content = f"""# Sessão de Destilação: {date_str}
- **Fonte**: {source_type} ({source_ref})
- **Domínio**: {domain}
- **Volatilidade da Fonte**: {volatility}
- **Triagem**: {classification}
- **Data/Hora**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Etapa 1: Desconstrutor Atômico
{etapa1_output}

## Etapa 2: Tecelão Nexialista
{etapa2_output}

## Etapa 3: Refatorador Ontológico (Diff Semântico)
{etapa3_output}
"""
    with open(session_filepath, 'w', encoding='utf-8') as f:
        f.write(session_content)
    log_success(f"Log de sessão salvo com sucesso em: {session_filepath}")

def cmd_refatorar(args):
    """Runs the Loop de Auto-Regeneração (Ciclo de Refatoração)."""
    canonicos_path = os.path.join(ONTOLOGIA_DIR, 'principios_canonicos.md')
    lacunas_path = os.path.join(ONTOLOGIA_DIR, 'lacunas_abertas.md')
    log_path = os.path.join(ONTOLOGIA_DIR, 'log_refatoracoes.md')

    if not os.path.exists(canonicos_path) or not os.path.exists(lacunas_path):
        log_error("Arquivos de ontologia em falta. Execute 'init' e tenha dados para refatorar.")
        sys.exit(1)

    with open(canonicos_path, 'r', encoding='utf-8') as f:
        principios = f.read()
    with open(lacunas_path, 'r', encoding='utf-8') as f:
        lacunas = f.read()

    generate = get_generator_with_fallback(args)

    log_info("Iniciando Loop de Auto-Regeneração (Ciclo de Refatoração)...")
    refatorador_prompt = load_template_file('refatorador_ciclo.md', {
        "PRINCIPIOS_CANONICOS": principios,
        "LACUNAS_ABERTAS": lacunas
    })

    result = generate(refatorador_prompt)
    parts = result.split("=== DIVIDER ===")

    if len(parts) < 3:
        log_error("Erro de formato na resposta do LLM. Esperava-se separadores '=== DIVIDER ==='.")
        print("\nResposta bruta:")
        print(result)
        sys.exit(1)

    new_principios_content = parts[0].strip()
    new_lacunas_content = parts[1].strip()
    report_content = parts[2].strip()

    # Backups
    create_backup(canonicos_path)
    create_backup(lacunas_path)
    create_backup(log_path)

    # Write new ontology files
    with open(canonicos_path, 'w', encoding='utf-8') as f:
        f.write(new_principios_content + "\n")
    with open(lacunas_path, 'w', encoding='utf-8') as f:
        f.write(new_lacunas_content + "\n")

    # Append report to log_refatoracoes.md
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"\n## Refatoração de Ciclo - {timestamp}\n")
        f.write(report_content + "\n")
        f.write("\n---\n")

    log_success("Ciclo de refatoração executado com sucesso!")
    print(f"\n{Colors.BOLD}=== RELATÓRIO DE MODIFICAÇÕES ==={Colors.ENDC}")
    print(report_content)
    print("=================================\n")

def cmd_auditar(args):
    """Runs the Auditoria Socrática on the base."""
    canonicos_path = os.path.join(ONTOLOGIA_DIR, 'principios_canonicos.md')
    if not os.path.exists(canonicos_path):
        log_error("Arquivo de princípios canônicos não encontrado. Inicialize a base primeiro.")
        sys.exit(1)

    with open(canonicos_path, 'r', encoding='utf-8') as f:
        principios = f.read()

    generate = get_generator_with_fallback(args)
    provider = getattr(generate, 'last_provider', 'unknown')
    model = getattr(generate, 'last_model', 'unknown')

    log_info("Iniciando Auditoria Socrática...")
    audit_prompt = load_template_file('auditoria_socrática.md', {
        "RESUMO_BASE_EXISTENTE": principios
    })

    result = generate(audit_prompt)
    provider = getattr(generate, 'last_provider', provider)
    model = getattr(generate, 'last_model', model)
    
    # Parse JSON structured output
    cleaned_result = result.strip()
    # Strip markdown wrapper if present
    if cleaned_result.startswith("```"):
        lines = cleaned_result.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned_result = "\n".join(lines).strip()
        
    audit_data = None
    try:
        audit_data = json.loads(cleaned_result)
    except Exception:
        # Regex search fallback
        match = re.search(r'\[\s*\{.*\}\s*\]', cleaned_result, re.DOTALL)
        if match:
            try:
                audit_data = json.loads(match.group(0))
            except Exception:
                pass
                
    if audit_data and isinstance(audit_data, list):
        auditorias_dir = os.path.join(ONTOLOGIA_DIR, 'auditorias')
        if not os.path.exists(auditorias_dir):
            os.makedirs(auditorias_dir)
            log_success(f"Diretório de auditorias criado: {auditorias_dir}")
            
        date_str = datetime.now().strftime("%Y-%m-%d")
        audit_filepath = os.path.join(auditorias_dir, f"{date_str}_auditoria.json")
        counter = 1
        while os.path.exists(audit_filepath):
            audit_filepath = os.path.join(auditorias_dir, f"{date_str}_auditoria_{counter}.json")
            counter += 1
            
        with open(audit_filepath, 'w', encoding='utf-8') as f:
            json.dump(audit_data, f, indent=4)
        log_success(f"Auditoria estruturada salva em: {audit_filepath}")
        
        print(f"\n{Colors.BOLD}=== AUDITORIA SOCRÁTICA DO SISTEMA ==={Colors.ENDC}")
        for idx, item in enumerate(audit_data, 1):
            print(f"\n{Colors.BLUE}{idx}. PROBLEMA:{Colors.ENDC} {item.get('problema')}")
            print(f"   {Colors.GREEN}PROPOSTA:{Colors.ENDC} {item.get('proposta')}")
            print(f"   {Colors.CYAN}EXPERIMENTO:{Colors.ENDC} {item.get('experimento')}")
        print("\n=====================================\n")
    else:
        log_warning("Resposta não estruturada ou JSON inválido recebido. Salvando formato livre.")
        print(result.strip())
        
        # Save format-free fallback
        date_str = datetime.now().strftime("%Y-%m-%d")
        audit_filename = f"{date_str}_auditoria_socratica.md"
        audit_filepath = os.path.join(SESSOES_DIR, audit_filename)
        counter = 1
        while os.path.exists(audit_filepath):
            audit_filename = f"{date_str}_auditoria_socratica_{counter}.md"
            audit_filepath = os.path.join(SESSOES_DIR, audit_filename)
            counter += 1

        audit_log = f"""# Auditoria Socrática do Sistema de Conhecimento
- **Data/Hora**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Provedor**: {provider}
- **Modelo**: {model}

{result.strip()}
"""
        with open(audit_filepath, 'w', encoding='utf-8') as f:
            f.write(audit_log)
        log_success(f"Resultado da auditoria salvo em formato livre em: {audit_filepath}")

# Helper Functions
def get_input_content(args):
    """Reads input content from text, file, or url."""
    if args.text:
        return args.text
    elif args.file:
        # Code specific optimization (Section 6)
        if args.source_type.lower() == "code" and os.path.isdir(args.file):
            content_parts = []
            for doc in ["README.md", "CHANGELOG.md", "README", "CHANGELOG"]:
                doc_path = os.path.join(args.file, doc)
                if os.path.exists(doc_path):
                    log_info(f"Lendo documento de repositório: {doc}...")
                    with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content_parts.append(f"=== {doc} ===\n" + f.read())
            if content_parts:
                return "\n\n".join(content_parts)
            else:
                log_warning(f"Diretório fornecido, mas nenhum README.md ou CHANGELOG.md encontrado em {args.file}.")

        if not os.path.exists(args.file):
            log_error(f"Arquivo não encontrado: {args.file}")
            sys.exit(1)
        with open(args.file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if args.file.lower().endswith(('.html', '.htm')):
            parser = HTMLTextExtractor()
            parser.feed(content)
            content = parser.get_text()
            content = re.sub(r'\n+', '\n', content)
        return content
    elif args.url:
        return fetch_url_text(args.url)
    return None

def get_provider_and_key(args):
    """Determines LLM provider, model, and resolves the API key."""
    provider = args.provider
    model = args.model
    api_key = args.api_key

    if not provider:
        # Autodetect from env/config
        det_provider, det_model, det_key = autodetect_provider_and_model()
        if det_provider:
            provider = det_provider
            model = model or det_model
            api_key = det_key
            log_info(f"Provedor autodetectado: {provider} (usando {model})")
        else:
            log_error("Nenhum provedor de LLM configurado ou detectado. Defina chaves de API no ambiente (.env) ou arquivo config.json.")
            sys.exit(1)
    else:
        # Provider explicitly provided, resolve key
        api_key = resolve_api_key(provider, api_key)
        if not api_key:
            log_error(f"Chave de API para o provedor '{provider}' não encontrada. Defina no ambiente ou config.json.")
            sys.exit(1)
        if not model:
            default_models = {
                "openai": "gpt-4o-mini",
                "anthropic": "claude-3-5-sonnet-20240620",
                "gemini": "gemini-1.5-flash",
                "huggingface": "meta-llama/Llama-3.3-70B-Instruct"
            }
            model = default_models.get(provider)
            log_info(f"Modelo não especificado. Usando o padrão para {provider}: {model}")

    return provider, model, api_key

def get_generator_with_fallback(args):
    """
    Returns a generate function that resolves all configured API keys
    and automatically falls back/rotates to the next available provider if one fails.
    """
    available_providers = []
    
    cli_provider = args.provider
    cli_model = args.model
    cli_key = args.api_key
    
    rotation_order = ["openai", "anthropic", "gemini", "huggingface", "agent"]
    
    if cli_provider:
        if cli_provider in rotation_order:
            rotation_order.remove(cli_provider)
        rotation_order.insert(0, cli_provider)
        
    for prov in rotation_order:
        keys = resolve_all_api_keys(prov, cli_key if prov == cli_provider else None)
        for key in keys:
            model = cli_model if (prov == cli_provider and cli_model) else None
            if not model:
                default_models = {
                    "openai": "gpt-4o-mini",
                    "anthropic": "claude-3-5-sonnet-20240620",
                    "gemini": "gemini-1.5-flash",
                    "huggingface": "meta-llama/Llama-3.3-70B-Instruct",
                    "agent": "self",
                    "antigravity": "self"
                }
                model = default_models.get(prov)
            available_providers.append((prov, model, key))
            
    if not available_providers:
        log_error("Nenhum provedor de LLM configurado ou detectado. Defina chaves de API no ambiente (.env) ou arquivo config.json.")
        sys.exit(1)
        
    def generate_with_rotation(prompt):
        last_exception = None
        for prov, model, key in available_providers:
            try:
                generate_with_rotation.last_provider = prov
                generate_with_rotation.last_model = model
                generator_fn = get_generator(prov, model, key, args.temperature)
                return generator_fn(prompt)
            except Exception as e:
                last_exception = e
                log_warning(f"O provedor {prov} ({model}) falhou: {e}. Tentando provedor de backup...")
        raise Exception(f"Todos os provedores de LLM configurados falharam. Último erro: {last_exception}")
        
    generate_with_rotation.last_provider = available_providers[0][0] if available_providers else None
    generate_with_rotation.last_model = available_providers[0][1] if available_providers else None
    return generate_with_rotation

def calculate_semantic_overlap(text1, text2):
    """Calculates vocabulary overlap (Jaccard similarity) between two texts."""
    def extract_words(text):
        if not text:
            return set()
        # Find alphanumeric words of length >= 3
        words = re.findall(r'\b\w{3,}\b', text.lower())
        return set(words)
        
    set1 = extract_words(text1)
    set2 = extract_words(text2)
    
    if not set1 or not set2:
        return 0.0
        
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)
def summarize_large_content(content, generate, max_chunk_size=20000):
    """Chunks large content and summarizes each chunk recursively, preventing token limits."""
    if not content or len(content) <= max_chunk_size:
        return content
        
    log_info(f"O conteúdo possui {len(content)} caracteres e excede o limite sugerido. Iniciando divisão semântica...")
    
    # Split content into chunks
    chunks = []
    current_idx = 0
    while current_idx < len(content):
        chunks.append(content[current_idx : current_idx + max_chunk_size])
        current_idx += max_chunk_size
        
    log_info(f"Total de fragmentos gerados: {len(chunks)}. Iniciando pré-destilação por fragmento...")
    
    summaries = []
    for idx, chunk in enumerate(chunks, 1):
        log_info(f"Processando fragmento {idx}/{len(chunks)}...")
        prompt = f"""
        [TAREFA]
        Analise o fragmento de conteúdo abaixo e extraia um resumo denso das principais entidades, domínios de conhecimento, links importantes e conceitos abordados.
        Mantenha a estrutura de rede e ignore boilerplates ou formatações repetitivas.
        
        Fragmento {idx}:
        ---
        {chunk}
        ---
        """
        try:
            summary = generate(prompt)
            summaries.append(summary.strip())
        except Exception as e:
            log_warning(f"Falha ao pré-processar fragmento {idx}: {e}")
            
    # Combine summaries
    combined = "\n\n=== FRAGMENT_BREAK ===\n\n".join(summaries)
    log_info("Pré-destilação concluída. Consolidando resumo final...")
    
    consolidation_prompt = f"""
    [TAREFA]
    Consolide os resumos dos fragmentos abaixo em um único documento estruturado e denso, preservando todos os domínios conceituais chave, redes de links importantes e tópicos principais identificados.
    
    Resumos dos fragmentos:
    ---
    {combined}
    ---
    """
    try:
        consolidated = generate(consolidation_prompt)
        return consolidated.strip()
    except Exception as e:
        log_error(f"Erro ao consolidar resumos: {e}")
        # Fallback to simple concatenation
        return "\n\n".join(summaries[:3])
def extract_classification(text):
    """Extracts classification code enclosed in brackets."""
    match = re.search(r'\[(RUÍDO-DE-BAIXA-DENSIDADE|REDUNDANTE-CONFIRMATIVO|CONFIRMAÇÃO-DE-AXIOMA|NÓ-NOVO-DE-CONHECIMENTO)\]', text)
    if match:
        return f"[{match.group(1)}]"
    return None

def fetch_github_starred(username=None):
    if not username:
        import subprocess
        log_info("Usuário do GitHub não fornecido. Buscando estrelas da conta autenticada via 'gh api'...")
        try:
            res = subprocess.run(["gh", "api", "user/starred"], capture_output=True, text=True, timeout=10)
            if res.returncode != 0:
                raise Exception(res.stderr)
            data = json.loads(res.stdout)
            result = []
            for repo in data:
                result.append({
                    "name": repo.get("full_name"),
                    "description": repo.get("description") or "Sem descrição",
                    "url": repo.get("html_url"),
                    "language": repo.get("language") or "Desconhecida"
                })
            return result
        except Exception as e:
            raise Exception(f"Erro ao buscar estrelas do GitHub via gh CLI: {e}")

    url = f"https://api.github.com/users/{username}/starred"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 promptcraft-cli"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
        result = []
        for repo in data:
            result.append({
                "name": repo.get("full_name"),
                "description": repo.get("description") or "Sem descrição",
                "url": repo.get("html_url"),
                "language": repo.get("language") or "Desconhecida"
            })
        return result
    except Exception as e:
        raise Exception(f"Erro ao buscar estrelas do GitHub: {e}")

def fetch_semantic_scholar_recommendations(arxiv_id):
    url = f"https://api.semanticscholar.org/recommendations/v1/papers/forpaper/arXiv:{arxiv_id}?limit=3"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 promptcraft-cli"}
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode('utf-8'))
        recommendations = data.get("recommendedPapers", [])
        result = []
        for paper in recommendations:
            result.append({
                "title": paper.get("title") or "Sem título",
                "url": paper.get("url") or "",
                "summary": paper.get("abstract") or "Sem abstract disponível"
            })
        return result
    except Exception as e:
        log_warning(f"Erro ao buscar adjacências no Semantic Scholar: {e}")
        return []

def fetch_arxiv_metadata(query_or_ids):
    if re.match(r'^\d{4}\.\d{4,5}', query_or_ids) or "," in query_or_ids:
        url = f"http://export.arxiv.org/api/query?id_list={query_or_ids}"
    else:
        escaped_query = urllib.parse.quote(query_or_ids)
        url = f"http://export.arxiv.org/api/query?search_query=all:{escaped_query}&max_results=5"
        
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 promptcraft-cli"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read().decode('utf-8')
        
        entries = re.findall(r'<entry>.*?</entry>', xml_data, re.DOTALL)
        result = []
        for entry in entries:
            title_match = re.search(r'<title>(.*?)</title>', entry, re.DOTALL)
            summary_match = re.search(r'<summary>(.*?)</summary>', entry, re.DOTALL)
            id_match = re.search(r'<id>(.*?)</id>', entry)
            
            title = re.sub(r'\s+', ' ', title_match.group(1).strip()) if title_match else "Sem título"
            summary = re.sub(r'\s+', ' ', summary_match.group(1).strip()) if summary_match else "Sem resumo"
            link = id_match.group(1).strip() if id_match else ""
            
            result.append({
                "title": title,
                "summary": summary,
                "url": link
            })
        return result
    except Exception as e:
        raise Exception(f"Erro ao buscar arXiv: {e}")

def parse_bookmarks_html(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    # Extract <A HREF="...">text</A>
    matches = re.findall(r'<A\s+[^>]*HREF=["\']([^"\']+)["\'][^>]*>(.*?)</A>', content, re.IGNORECASE | re.DOTALL)
    result = []
    for url, title in matches:
        title_clean = re.sub(r'\s+', ' ', title).strip() or "Sem título"
        result.append({
            "url": url.strip(),
            "title": title_clean
        })
    return result

def parse_youtube_subscriptions(csv_path):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {csv_path}")
    
    result = []
    with open(csv_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read().lstrip('\ufeff')
        lines = content.splitlines()
        if not lines:
            return result
        
        reader = csv.reader(lines)
        header = next(reader, None)
        
        # Detect if it is a playlist CSV or subscriptions CSV
        is_playlist = False
        col_video_id = -1
        if header:
            header_joined = "".join(header).lower()
            if "vídeo" in header_joined or "video" in header_joined:
                is_playlist = True
                for idx, h in enumerate(header):
                    h_lower = h.lower().strip()
                    if "id" in h_lower:
                        col_video_id = idx
                        break
        
        if is_playlist and col_video_id != -1:
            for row in reader:
                if not row or len(row) <= col_video_id:
                    continue
                video_id = row[col_video_id].strip()
                result.append({
                    "id": video_id,
                    "title": f"Vídeo {video_id}",
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "type": "video"
                })
            return result
            
        col_id, col_title, col_url = 0, 1, 2
        if header:
            for idx, h in enumerate(header):
                h_lower = h.lower().strip()
                if "channel id" in h_lower or "id" in h_lower:
                    col_id = idx
                elif "channel title" in h_lower or "title" in h_lower or "nome" in h_lower or "título" in h_lower or "titulo" in h_lower:
                    col_title = idx
                elif "channel url" in h_lower or "url" in h_lower or "link" in h_lower:
                    col_url = idx
                    
        for row in reader:
            if not row or len(row) <= max(col_id, col_title, col_url):
                continue
            result.append({
                "id": row[col_id].strip(),
                "title": row[col_title].strip(),
                "url": row[col_url].strip(),
                "type": "channel"
            })
    return result

def parse_reddit_posts(file_path):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
    result = []
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read().strip()
        
    if content.startswith('[') or content.startswith('{'):
        try:
            data = json.loads(content)
            posts = data if isinstance(data, list) else [data]
            for p in posts:
                result.append({
                    "title": p.get("title") or p.get("body", "")[:100] or "Sem título",
                    "url": p.get("url") or p.get("permalink") or "",
                    "subreddit": p.get("subreddit") or "unknown",
                    "body": p.get("body") or p.get("selftext") or "Sem conteúdo"
                })
        except Exception as e:
            raise Exception(f"Erro ao parsear JSON do Reddit: {e}")
    else:
        # CSV parsing
        lines = content.splitlines()
        reader = csv.reader(lines)
        header = next(reader, None)
        col_title, col_url, col_sub = 0, 1, 2
        if header:
            for idx, h in enumerate(header):
                h_lower = h.lower().strip()
                if "title" in h_lower or "titulo" in h_lower or "título" in h_lower:
                    col_title = idx
                elif "url" in h_lower or "link" in h_lower or "permalink" in h_lower:
                    col_url = idx
                elif "subreddit" in h_lower or "sub" in h_lower:
                    col_sub = idx
        for row in reader:
            if not row:
                continue
            title = row[col_title].strip() if len(row) > col_title else "Sem título"
            url = row[col_url].strip() if len(row) > col_url else ""
            sub = row[col_sub].strip() if len(row) > col_sub else "reddit"
            result.append({
                "title": title,
                "url": url,
                "subreddit": sub,
                "body": ""
            })
    return result

def cmd_importar(args):
    """Parses and ingests external sources like YouTube, GitHub, Reddit, arXiv, bookmarks, gdrive, and snapshot."""
    import_type = args.type
    log_info(f"Iniciando importação de fontes do tipo '{import_type}'...")
    
    entries = []
    
    if import_type == "youtube":
        if not args.file:
            log_error("O parâmetro --file é obrigatório para importação do tipo youtube.")
            sys.exit(1)
        try:
            entries = parse_youtube_subscriptions(args.file)
            log_success(f"Carregadas {len(entries)} inscrições do YouTube.")
        except Exception as e:
            log_error(f"Falha ao ler inscrições: {e}")
            sys.exit(1)
            
    elif import_type == "github":
        try:
            entries = fetch_github_starred(args.user)
            user_label = args.user or "autenticada"
            log_success(f"Carregados {len(entries)} repositórios favoritados do GitHub para a conta {user_label}.")
        except Exception as e:
            log_error(f"Falha ao buscar favoritos do GitHub: {e}")
            sys.exit(1)
            
    elif import_type == "reddit":
        if not args.file:
            log_error("O parâmetro --file é obrigatório para importação do tipo reddit.")
            sys.exit(1)
        try:
            entries = parse_reddit_posts(args.file)
            log_success(f"Carregados {len(entries)} posts salvos do Reddit.")
        except Exception as e:
            log_error(f"Falha ao carregar posts do Reddit: {e}")
            sys.exit(1)
            
    elif import_type == "arxiv":
        if not args.query:
            log_error("O parâmetro --query é obrigatório para importação do tipo arxiv (IDs ou termo de busca).")
            sys.exit(1)
        try:
            entries = fetch_arxiv_metadata(args.query)
            log_success(f"Carregados {len(entries)} artigos do arXiv.")
            
            # For each entry, try to fetch Semantic Scholar recommendations (adjacent papers)
            adjacent_entries = []
            for entry in entries:
                arxiv_match = re.search(r'arxiv.org/abs/(\d{4}\.\d{4,5})', entry['url'])
                if arxiv_match:
                    arxiv_id = arxiv_match.group(1)
                    log_info(f"Buscando recomendações adjacentes para o paper {arxiv_id} no Semantic Scholar...")
                    recs = fetch_semantic_scholar_recommendations(arxiv_id)
                    adjacent_entries.extend(recs)
            
            if adjacent_entries:
                log_success(f"Encontrados {len(adjacent_entries)} artigos adjacentes no Semantic Scholar.")
                entries.extend(adjacent_entries)
        except Exception as e:
            log_error(f"Falha ao buscar artigos do arXiv: {e}")
            sys.exit(1)

    elif import_type == "bookmarks":
        if not args.file:
            log_error("O parâmetro --file é obrigatório para importação do tipo bookmarks (caminho para o html de favoritos).")
            sys.exit(1)
        try:
            entries = parse_bookmarks_html(args.file)
            log_success(f"Carregados {len(entries)} favoritos do arquivo {args.file}.")
            if len(entries) > 1000:
                log_warning(f"Alta quantidade de favoritos detectada ({len(entries)}). Limitando exibição para os primeiros 50 em fontes_importadas.md, mas salvando todos.")
                entries = entries[:50]
        except Exception as e:
            log_error(f"Falha ao ler favoritos: {e}")
            sys.exit(1)

    elif import_type == "gdrive":
        if not args.file:
            log_error("O parâmetro --file (remoto:pasta) é obrigatório para importação do tipo gdrive (ex: xinaya:Claude).")
            sys.exit(1)
        try:
            import subprocess
            local_dest = os.path.join(BASE_DIR, "takeout")
            os.makedirs(local_dest, exist_ok=True)
            log_info(f"Executando rclone copy de {args.file} para {local_dest}...")
            cmd = ["rclone", "copy", args.file, local_dest, "--max-depth", "2", "--include", "*.md", "--include", "*.txt", "--include", "*.pdf"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode == 0:
                log_success(f"Sincronização concluída com sucesso via rclone.")
                imported_files = []
                for root, _, files in os.walk(local_dest):
                    for f in files:
                        if f.endswith((".md", ".txt", ".pdf")):
                            imported_files.append(f)
                entries = [{"title": f, "url": f"file://{os.path.join(local_dest, f)}"} for f in imported_files[:50]]
            else:
                log_error(f"Erro no rclone: {res.stderr}")
                sys.exit(1)
        except Exception as e:
            log_error(f"Falha ao executar rclone: {e}")
            sys.exit(1)

    elif import_type == "snapshot":
        if not args.query:
            log_error("O parâmetro --query (space name, ex: uniswap ou aave.eth) é obrigatório para importação do tipo snapshot.")
            sys.exit(1)
        try:
            query = """
            query Proposals($space: String!) {
              proposals(
                first: 10,
                where: { space: $space, state: "closed" },
                orderBy: "created",
                orderDirection: desc
              ) {
                id
                title
                state
                author
              }
            }
            """
            import urllib.request
            payload = json.dumps({"query": query, "variables": {"space": args.query}})
            req = urllib.request.Request(
                "https://hub.snapshot.org/graphql",
                data=payload.encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                data = json.loads(res.read().decode("utf-8"))
                proposals = data.get("data", {}).get("proposals", [])
                entries = [{"title": p["title"], "url": f"https://snapshot.org/#/{args.query}/proposal/{p['id']}"} for p in proposals]
                log_success(f"Carregadas {len(entries)} propostas de governança da DAO {args.query}.")
        except Exception as e:
            log_error(f"Falha ao buscar propostas do Snapshot: {e}")
            sys.exit(1)
            
    # Write to fontes_importadas.md
    output_path = args.output or os.path.join(ONTOLOGIA_DIR, 'fontes_importadas.md')
    create_backup(output_path)
    
    # Generate content
    lines = []
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            existing_content = f.read().strip()
        lines.append(existing_content)
        lines.append(f"\n## Importação de {import_type.upper()} em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    else:
        lines.append(f"# Fontes Importadas\nRegistro consolidado de importações externas do ecossistema.\n")
        lines.append(f"## Importação de {import_type.upper()} em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
    for entry in entries:
        if import_type == "youtube":
            if entry.get("type") == "video":
                lines.append(f"- **Vídeo**: [{entry['title']}]({entry['url']}) (ID: `{entry['id']}`)")
            else:
                lines.append(f"- **Canal**: [{entry['title']}]({entry['url']}) (ID: `{entry['id']}`)")
        elif import_type == "github":
            lines.append(f"- **Repo**: [{entry['name']}]({entry['url']}) | Linguagem: `{entry['language']}`\n  *Descrição*: {entry['description']}")
        elif import_type == "reddit":
            lines.append(f"- **Reddit (r/{entry['subreddit']})**: [{entry['title']}]({entry['url']})\n  {entry['body'][:200]}...")
        elif import_type == "arxiv":
            lines.append(f"- **arXiv Paper**: [{entry['title']}]({entry['url']})\n  *Summary*: {entry['summary'][:300]}...")
        elif import_type == "bookmarks":
            lines.append(f"- **Bookmark**: [{entry['title']}]({entry['url']})")
        elif import_type == "gdrive":
            lines.append(f"- **GDrive File**: [{entry['title']}]({entry['url']})")
        elif import_type == "snapshot":
            lines.append(f"- **DAO Proposal**: [{entry['title']}]({entry['url']})")
            
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines) + "\n")
        
    log_success(f"Fontes importadas gravadas com sucesso em: {output_path}")

def cmd_pesquisar(args):
    r"""
    Executes the 4-step Loop Metacognitivo (Manifesto Oms-Sistêmico).
    
    Formalismo Simbólico (Seção 11):
      Gnosio-Logística (Passo 1): Identifica novas perguntas (L')
      Integração e Simulação (Passos 2-3): Processamento heurístico
      Compressão (Passo 4): Extração de invariantes
      A' = R(A ⊕ a_i)
      L' = L ∪ lacunas(a_i) \ respostas(a_i)
    """
    # 1. Resolve content (scope)
    content = get_input_content(args)
    if not content:
        log_error("Nenhum conteúdo de entrada (escopo) fornecido. Use --text, --file ou --url.")
        sys.exit(1)

    generate = get_generator_with_fallback(args)

    # Pre-distill large contents (Point 4 of scaling plan)
    content = summarize_large_content(content, generate)

    line = args.line

    log_info(f"Iniciando Loop Metacognitivo para a linha de pesquisa: '{line}'")
    
    # Passo 1: Gnosio-Logística
    log_info("Passo 1/4: Gnosio-Logística (Inquérito Essencial)...")
    p1_prompt = load_template_file('gnosio_logistica.md', {
        "LINHA_PESQUISA": line,
        "ESCOPO": content
    })
    p1_output = generate(p1_prompt)
    print(f"\n{Colors.GREEN}=== PASSO 1 (Gnosio-Logística) ==={Colors.ENDC}")
    print(p1_output.strip())
    
    # Passo 2: Integração de Frameworks
    log_info("Passo 2/4: Integração de Frameworks (Análise e Trade-Offs)...")
    p2_prompt = load_template_file('integrar_frameworks.md', {
        "PASSO1_OUTPUT": p1_output
    })
    p2_output = generate(p2_prompt)
    print(f"\n{Colors.GREEN}=== PASSO 2 (Integração de Frameworks) ==={Colors.ENDC}")
    print(p2_output.strip())
    
    # Passo 3: Simulação e Debug
    log_info("Passo 3/4: Simulação e Debug (Code Review Híbrido)...")
    p3_prompt = load_template_file('simulacao_codigo.md', {
        "PASSO2_OUTPUT": p2_output
    })
    p3_output = generate(p3_prompt)
    print(f"\n{Colors.GREEN}=== PASSO 3 (Simulação e Debug) ==={Colors.ENDC}")
    print(p3_output.strip())
    
    # Passo 4: Compressão de Sabedoria
    log_info("Passo 4/4: Compressão de Sabedoria...")
    p4_prompt = load_template_file('compressao_sabedoria.md', {
        "PASSO3_OUTPUT": p3_output
    })
    p4_output = generate(p4_prompt)
    print(f"\n{Colors.GREEN}=== PASSO 4 (Compressão de Sabedoria) ==={Colors.ENDC}")
    print(p4_output.strip())

    # Write output session
    provider = getattr(generate, 'last_provider', 'unknown')
    model = getattr(generate, 'last_model', 'unknown')
    date_str = datetime.now().strftime("%Y-%m-%d")
    sanitized_line = re.sub(r'[^a-zA-Z0-9_-]', '_', line.lower())
    session_filename = f"{date_str}_inquiry_{sanitized_line}.md"
    session_filepath = os.path.join(SESSOES_DIR, session_filename)
    
    # Ensure unique file name if it already exists
    counter = 1
    while os.path.exists(session_filepath):
        session_filename = f"{date_str}_inquiry_{sanitized_line}_{counter}.md"
        session_filepath = os.path.join(SESSOES_DIR, session_filename)
        counter += 1

    session_content = f"""# Pesquisa Sistemática: {line}
- **Data/Hora**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Provedor/Modelo**: {provider} ({model})

## Passo 1: Gnosio-Logística (Inquérito Essencial)
{p1_output}

## Passo 2: Integração de Frameworks (Análise e Trade-Offs)
{p2_output}

## Passo 3: Simulação e Debug (Code Review Híbrido)
{p3_output}

## Passo 4: Compressão de Sabedoria
{p4_output}
"""
    with open(session_filepath, 'w', encoding='utf-8') as f:
        f.write(session_content)
    log_success(f"Relatório de pesquisa salvo em: {session_filepath}")

    # Integrate Passo 4 wisdom and gaps into the base
    log_info("Integrando sabedoria e lacunas obtidas na base da ontologia...")
    canonicos_path = os.path.join(ONTOLOGIA_DIR, 'principios_canonicos.md')
    lacunas_path = os.path.join(ONTOLOGIA_DIR, 'lacunas_abertas.md')
    
    current_principles = ""
    if os.path.exists(canonicos_path):
        with open(canonicos_path, 'r', encoding='utf-8') as f:
            current_principles = f.read()
            
    current_gaps = ""
    if os.path.exists(lacunas_path):
        with open(lacunas_path, 'r', encoding='utf-8') as f:
            current_gaps = f.read()

    integration_prompt = f"""
    Base Canônica Atual (`principios_canonicos.md`):
    ---
    {current_principles}
    ---
    
    Resultados de Pesquisa (Passo 4):
    ---
    {p4_output}
    ---
    
    [TAREFA]
    Incorpore o conhecimento e diretrizes regenerativas obtidas no Passo 4 na Base Canônica.
    Retorne APENAS o novo conteúdo completo de `principios_canonicos.md` formatado em Markdown. Não adicione preamble ou comentários.
    """
    new_principles = generate(integration_prompt)
    
    # Assert Seção 11 Invariante: A' = R(A ⊕ a_i)
    assert len(new_principles.strip()) > 0, "Erro Invariante: A nova base canônica (A') está vazia após a pesquisa."
    if len(current_principles.strip()) > 100:
        assert len(new_principles.strip()) >= 0.7 * len(current_principles.strip()), "Erro Invariante: A base canônica (A') sofreu compressão catastrófica (>30% de perda)."

    create_backup(canonicos_path)
    with open(canonicos_path, 'w', encoding='utf-8') as f:
        f.write(new_principles.strip() + "\n")
        
    gaps_prompt = f"""
    Lacunas Abertas Atuais (`lacunas_abertas.md`):
    ---
    {current_gaps}
    ---
    
    Gaps e Questões geradas no Passo 1 e nos resultados de pesquisa:
    ---
    {p1_output}
    ---
    
    [TAREFA]
    Incorpore as novas perguntas essenciais e lacunas geradas na lista de lacunas abertas. Remova qualquer pergunta que já foi respondida.
    Retorne APENAS o novo conteúdo completo de `lacunas_abertas.md` em Markdown. Não adicione preamble ou comentários.
    """
    new_gaps = generate(gaps_prompt)
    
    # Assert Seção 11 Invariante: L' = L ∪ lacunas(a_i) \ respostas(a_i)
    assert len(new_gaps.strip()) > 0, "Erro Invariante: O novo arquivo de lacunas (L') está vazio após a pesquisa."

    create_backup(lacunas_path)
    with open(lacunas_path, 'w', encoding='utf-8') as f:
        f.write(new_gaps.strip() + "\n")

    # Calculate Jaccard overlap for Convergence Criterion (Point ⑦)
    overlap = calculate_semantic_overlap(p4_output, current_principles)
    log_info(f"Sobreposição semântica (Jaccard) detectada: {overlap:.2%}")
    if overlap > 0.8:
        log_success("[CONVERGÊNCIA DETECTADA] O output do Passo 4 apresenta alta convergência semântica (>80%) com a base canônica atual.")

    # Save to log_refatoracoes.md (Point ⑥)
    log_path = os.path.join(ONTOLOGIA_DIR, 'log_refatoracoes.md')
    create_backup(log_path)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(f"\n## Pesquisa Sistemática - {timestamp}\n")
        f.write(f"- **Linha de Pesquisa**: {line}\n")
        f.write(f"- **Convergência Semântica**: {overlap:.2%} (Limiar: 80.00%)\n")
        if overlap > 0.8:
            f.write(f"- **Status**: [CONVERGÊNCIA DETECTADA]\n")
        else:
            f.write(f"- **Status**: Evolução Contínua\n")
        f.write(f"\n### Compressão de Sabedoria (Passo 4)\n")
        f.write(p4_output.strip() + "\n")
        f.write("\n---\n")
    log_success("Resultados da pesquisa e compressão registrados no log de refatorações.")
        
    log_success("Ontologia atualizada com os novos ensinamentos e lacunas obtidas!")
def cmd_bump_template(args):
    """Bumps the version of a template file matching the spec schema: {nome}__v{major}.{minor}.md"""
    template_name = args.name
    level = args.level
    
    if not os.path.exists(TEMPLATES_DIR):
        log_error(f"Diretório de templates não existe: {TEMPLATES_DIR}")
        sys.exit(1)
        
    files = os.listdir(TEMPLATES_DIR)
    
    base_search = template_name
    if base_search.endswith(".md"):
        base_search = base_search[:-3]
    if "__v" in base_search:
        base_search = base_search.split("__v")[0]
        
    matched_file = None
    current_major = 1
    current_minor = 0
    
    for f in files:
        if not f.endswith(".md"):
            continue
        f_base = f[:-3]
        f_clean = f_base.split("__v")[0]
        
        if f_clean == base_search:
            matched_file = f
            if "__v" in f_base:
                ver_part = f_base.split("__v")[1]
                match = re.match(r'^(\d+)\.(\d+)$', ver_part)
                if match:
                    current_major = int(match.group(1))
                    current_minor = int(match.group(2))
            break
            
    if not matched_file:
        log_error(f"Nenhum template correspondente a '{template_name}' encontrado em {TEMPLATES_DIR}")
        sys.exit(1)
        
    if level == "major":
        new_major = current_major + 1
        new_minor = 0
    else:
        new_major = current_major
        new_minor = current_minor + 1
        
    new_filename = f"{base_search}__v{new_major}.{new_minor}.md"
    old_path = os.path.join(TEMPLATES_DIR, matched_file)
    new_path = os.path.join(TEMPLATES_DIR, new_filename)
    
    os.rename(old_path, new_path)
    log_success(f"Template renomeado com sucesso de '{matched_file}' para '{new_filename}'")

def main():
    parser = argparse.ArgumentParser(
        description="Motor Nexialista de Destilação de Conhecimento - CLI de Engenharia de Prompts",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(title="comandos", dest="command", required=True)

    # Command init
    subparsers.add_parser("init", help="Inicializa a estrutura de pastas e configurações padrão.")

    # Command triar
    parser_triar = subparsers.add_parser("triar", help="Executa a triagem (Filtro P1-P3) de uma fonte.")
    
    # Command processar
    parser_proc = subparsers.add_parser("processar", help="Processa uma fonte pelo pipeline completo (Etapas 1-3) e atualiza a ontologia.")

    # Command refatorar
    subparsers.add_parser("refatorar", help="Executa o Ciclo de Refatoração / Loop de Auto-Regeneração da ontologia.")

    # Command auditar
    subparsers.add_parser("auditar", help="Executa a Auditoria Socrática do sistema de conhecimento.")

    # Command importar
    parser_imp = subparsers.add_parser("importar", help="Importa fontes externas (YouTube, GitHub, Reddit, arXiv) para o catálogo.")
    parser_imp.add_argument("--type", choices=["youtube", "github", "reddit", "arxiv", "bookmarks", "gdrive", "snapshot"], required=True, help="Tipo de fonte para importação.")
    parser_imp.add_argument("--file", help="Caminho do arquivo local (obrigatório para youtube/reddit).")
    parser_imp.add_argument("--user", help="Username do GitHub (obrigatório para github).")
    parser_imp.add_argument("--query", help="Termo de pesquisa ou lista de IDs (obrigatório para arxiv).")
    parser_imp.add_argument("--output", help="Arquivo de destino (default: ontologia/fontes_importadas.md).")

    # Command pesquisar
    parser_pesq = subparsers.add_parser("pesquisar", help="Executa o Loop Metacognitivo (4 etapas) para deep research.")
    group_pesq = parser_pesq.add_mutually_exclusive_group(required=True)
    group_pesq.add_argument("--text", help="Texto de escopo.")
    group_pesq.add_argument("--file", help="Arquivo local contendo dados de escopo.")
    group_pesq.add_argument("--url", help="URL do site contendo dados de escopo.")
    parser_pesq.add_argument("--line", default="Engenharia Simbólica de Portfólios Regenerativos", help="Linha de pesquisa / tema principal.")
    parser_pesq.add_argument("--provider", choices=["openai", "anthropic", "gemini", "huggingface", "agent", "antigravity"], help="Provedor do LLM.")
    parser_pesq.add_argument("--model", help="Modelo de LLM específico.")
    parser_pesq.add_argument("--api-key", help="Chave de API manual.")
    parser_pesq.add_argument("--temperature", type=float, default=0.2, help="Temperatura (default: 0.2).")

    # Command bump-template
    parser_bump = subparsers.add_parser("bump-template", help="Versiona um template de prompt incrementando minor ou major.")
    parser_bump.add_argument("--name", required=True, help="Nome do arquivo ou base do template (ex: desconstrutor_atomico).")
    parser_bump.add_argument("--level", choices=["major", "minor"], default="minor", help="Nível do incremento semver (default: minor).")

    # Add arguments to source/process inputs
    for p in [parser_triar, parser_proc]:
        group = p.add_mutually_exclusive_group(required=True)
        group.add_argument("--text", help="Texto direto a ser processado.")
        group.add_argument("--file", help="Caminho do arquivo local (ou pasta, no caso de repositório de código).")
        group.add_argument("--url", help="URL do site para obter o conteúdo.")

        # Provider configurations
        p.add_argument("--provider", choices=["openai", "anthropic", "gemini", "huggingface", "agent", "antigravity"], help="Provedor do LLM.")
        p.add_argument("--model", help="Modelo de LLM específico (ex: gpt-4o, claude-3-5-sonnet-20240620, gemini-1.5-pro).")
        p.add_argument("--api-key", help="Chave de API manual para o provedor.")
        p.add_argument("--temperature", type=float, default=0.2, help="Temperatura para a geração (default: 0.2).")

    # Specific configurations for 'processar'
    parser_proc.add_argument("--source-type", choices=["video", "document", "code", "feed", "data", "personal", "bookmark"], default="document", help="Tipo da fonte para classificação (default: document).")
    parser_proc.add_argument("--source-ref", default="manual-input", help="Referência/identificador da fonte (ex: URL ou nome do autor).")
    parser_proc.add_argument("--domain", default="domínio-próprio", help="Domínio epistemológico da fonte (default: domínio-próprio).")
    parser_proc.add_argument("--force", action="store_true", help="Força o processamento mesmo que a triagem rotule a fonte como ruído ou redundante.")

    # Provider configurations for command 'refatorar' and 'auditar'
    for p in [subparsers.choices["refatorar"], subparsers.choices["auditar"]]:
        p.add_argument("--provider", choices=["openai", "anthropic", "gemini", "huggingface", "agent", "antigravity"], help="Provedor do LLM.")
        p.add_argument("--model", help="Modelo de LLM específico.")
        p.add_argument("--api-key", help="Chave de API manual.")
        p.add_argument("--temperature", type=float, default=0.2, help="Temperatura (default: 0.2).")

    args = parser.parse_args()

    # Execute commands
    if args.command == "init":
        cmd_init(args)
    elif args.command == "triar":
        cmd_triar(args)
    elif args.command == "processar":
        cmd_processar(args)
    elif args.command == "refatorar":
        cmd_refatorar(args)
    elif args.command == "auditar":
        cmd_auditar(args)
    elif args.command == "importar":
        cmd_importar(args)
    elif args.command == "pesquisar":
        cmd_pesquisar(args)
    elif args.command == "bump-template":
        cmd_bump_template(args)

if __name__ == "__main__":
    main()
