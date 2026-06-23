import os
import tempfile
import pytest
from promptcraft import (
    load_env,
    HTMLTextExtractor,
    substitute_template,
    extract_classification,
    VOLATILITY_SCORES,
    parse_youtube_subscriptions,
    parse_reddit_posts,
    get_volatility_score,
    calculate_semantic_overlap,
    summarize_large_content
)

def test_load_env():
    # Create a temporary env file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write("# This is a comment\n")
        f.write("KEY1=VALUE1\n")
        f.write("KEY2=\"VALUE2\"\n")
        f.write("  KEY3 = 'VALUE3'  \n")
        f.write("EMPTY_KEY=\n")
        temp_path = f.name

    try:
        vars_dict = load_env(temp_path)
        assert vars_dict["KEY1"] == "VALUE1"
        assert vars_dict["KEY2"] == "VALUE2"
        assert vars_dict["KEY3"] == "VALUE3"
        assert vars_dict["EMPTY_KEY"] == ""
    finally:
        os.remove(temp_path)

def test_substitute_template():
    template = "Olá {NOME}, bem-vindo ao {SISTEMA}. Seu papel é {PAPEL}."
    variables = {
        "NOME": "Alice",
        "SISTEMA": "Motor Nexialista",
        "PAPEL": "Axiólogo"
    }
    result = substitute_template(template, variables)
    assert result == "Olá Alice, bem-vindo ao Motor Nexialista. Seu papel é Axiólogo."

    # Test single braces that shouldn't be touched unless matched
    template2 = "Olá {NOME}, brackets extras {INC} no match {IGNORE}."
    variables2 = {"NOME": "Bob", "INC": "aqui"}
    result2 = substitute_template(template2, variables2)
    assert result2 == "Olá Bob, brackets extras aqui no match {IGNORE}."

def test_html_text_extractor():
    html = """
    <html>
        <head>
            <style>body { color: red; }</style>
            <script>console.log("hello");</script>
            <title>Ignorado no body</title>
        </head>
        <body>
            <header>Cabeçalho Ignorado</header>
            <nav>Navegação Ignorada</nav>
            <h1>Título do Artigo</h1>
            <p>Este é o primeiro parágrafo com um <a href="https://example.com">link de teste</a>.</p>
            <div>
                <span>Texto aninhado.</span>
            </div>
            <footer>Rodapé Ignorado</footer>
        </body>
    </html>
    """
    parser = HTMLTextExtractor()
    parser.feed(html)
    text = parser.get_text()
    
    # Check that script/style/nav/header/footer content is ignored
    assert "console.log" not in text
    assert "color: red" not in text
    assert "Cabeçalho Ignorado" not in text
    assert "Navegação Ignorada" not in text
    assert "Rodapé Ignorado" not in text
    
    # Check that correct body elements are extracted
    assert "Título do Artigo" in text
    assert "[link de teste](https://example.com)" in text
    assert "Texto aninhado." in text

def test_extract_classification():
    assert extract_classification("O resultado da triagem é [NÓ-NOVO-DE-CONHECIMENTO]") == "[NÓ-NOVO-DE-CONHECIMENTO]"
    assert extract_classification("Classificou como [RUÍDO-DE-BAIXA-DENSIDADE] por ser propaganda.") == "[RUÍDO-DE-BAIXA-DENSIDADE]"
    assert extract_classification("Base canônica já contém [REDUNDANTE-CONFIRMATIVO]") == "[REDUNDANTE-CONFIRMATIVO]"
    assert extract_classification("[CONFIRMAÇÃO-DE-AXIOMA] porque confirma a lei de Zipf.") == "[CONFIRMAÇÃO-DE-AXIOMA]"
    assert extract_classification("Não tem classificação correta") is None

def test_volatility_scores():
    assert get_volatility_score("video") == 5
    assert get_volatility_score("code") == 8
    assert get_volatility_score("data") == 10
    assert get_volatility_score("unknown") == 5

def test_parse_youtube_subscriptions():
    csv_content = """Channel Id,Channel Title,Channel URL
UC123,Cozinha de Vanguarda,https://youtube.com/c/cozinha
UC456,Hard Tech Show,https://youtube.com/c/hardtech
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write(csv_content)
        temp_path = f.name
        
    try:
        channels = parse_youtube_subscriptions(temp_path)
        assert len(channels) == 2
        assert channels[0]["id"] == "UC123"
        assert channels[0]["title"] == "Cozinha de Vanguarda"
        assert channels[0]["url"] == "https://youtube.com/c/cozinha"
        assert channels[1]["id"] == "UC456"
        assert channels[1]["title"] == "Hard Tech Show"
        assert channels[1]["url"] == "https://youtube.com/c/hardtech"
    finally:
        os.remove(temp_path)

    # Test Portuguese headers (Takeout format)
    csv_pt = """ID do canal,URL do canal,Título do canal
UC789,https://youtube.com/c/novotempo,Novo Tempo
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write(csv_pt)
        temp_path_pt = f.name
        
    try:
        channels_pt = parse_youtube_subscriptions(temp_path_pt)
        assert len(channels_pt) == 1
        assert channels_pt[0]["id"] == "UC789"
        assert channels_pt[0]["title"] == "Novo Tempo"
        assert channels_pt[0]["url"] == "https://youtube.com/c/novotempo"
    finally:
        os.remove(temp_path_pt)

def test_parse_reddit_posts():
    # Test JSON format
    reddit_json = """[
        {"title": "Mecanismo Causal A", "permalink": "https://reddit.com/r/science/a", "subreddit": "science", "body": "Explicação do mecanismo..."},
        {"title": "Teoria B", "permalink": "https://reddit.com/r/philosophy/b", "subreddit": "philosophy", "body": "Estudo de caso..."}
    ]"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write(reddit_json)
        temp_json_path = f.name
        
    try:
        posts = parse_reddit_posts(temp_json_path)
        assert len(posts) == 2
        assert posts[0]["title"] == "Mecanismo Causal A"
        assert posts[0]["url"] == "https://reddit.com/r/science/a"
        assert posts[0]["subreddit"] == "science"
        assert posts[0]["body"] == "Explicação do mecanismo..."
    finally:
        os.remove(temp_json_path)

    # Test CSV format
    reddit_csv = """Title,URL,Subreddit
Mecanismo Causal C,https://reddit.com/r/science/c,science
"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, encoding='utf-8') as f:
        f.write(reddit_csv)
        temp_csv_path = f.name
        
    try:
        posts = parse_reddit_posts(temp_csv_path)
        assert len(posts) == 1
        assert posts[0]["title"] == "Mecanismo Causal C"
        assert posts[0]["url"] == "https://reddit.com/r/science/c"
        assert posts[0]["subreddit"] == "science"
    finally:
        os.remove(temp_csv_path)

def test_bump_template_and_dynamic_version_loading(monkeypatch):
    import promptcraft
    with tempfile.TemporaryDirectory() as temp_dir:
        monkeypatch.setattr(promptcraft, "TEMPLATES_DIR", temp_dir)
        
        # 1. Create a dummy template without version
        dummy_name = "test_template.md"
        dummy_path = os.path.join(temp_dir, dummy_name)
        with open(dummy_path, 'w', encoding='utf-8') as f:
            f.write("Versão original de {NOME}")
            
        # Verify it loads correctly
        loaded_orig = promptcraft.load_template_file(dummy_name, {"NOME": "Alice"})
        assert loaded_orig == "Versão original de Alice"
        
        # 2. Bump template to minor
        class ArgsMock:
            name = "test_template"
            level = "minor"
            
        promptcraft.cmd_bump_template(ArgsMock())
        
        # File should be renamed to test_template__v1.1.md (default major=1, bumped minor=1)
        assert os.path.exists(os.path.join(temp_dir, "test_template__v1.1.md"))
        assert not os.path.exists(dummy_path)
        
        # Verify load_template_file still finds and loads it using "test_template"
        loaded_bump = promptcraft.load_template_file("test_template", {"NOME": "Bob"})
        assert loaded_bump == "Versão original de Bob"
        
        # Write another version: test_template__v2.0.md
        with open(os.path.join(temp_dir, "test_template__v2.0.md"), 'w', encoding='utf-8') as f:
            f.write("Versão 2.0 de {NOME}")
            
        # Verify it automatically loads the highest version (v2.0)
        loaded_v2 = promptcraft.load_template_file("test_template", {"NOME": "Carlos"})
        assert loaded_v2 == "Versão 2.0 de Carlos"

def test_calculate_semantic_overlap():
    text1 = "Axioma da complexidade e integridade semântica."
    text2 = "Axioma da complexidade e regeneração sistêmica."
    # Unique words >= 3:
    # text1: {"axioma", "complexidade", "integridade", "semantica"} (4 words)
    # text2: {"axioma", "complexidade", "regeneracao", "sistemica"} (4 words)
    # Intersection: {"axioma", "complexidade"} (2 words)
    # Union: {"axioma", "complexidade", "integridade", "semantica", "regeneracao", "sistemica"} (6 words)
    # Jaccard = 2/6 = 0.3333333333333333
    overlap = calculate_semantic_overlap(text1, text2)
    assert abs(overlap - 2/6) < 1e-5

    # Check identical texts
    assert calculate_semantic_overlap(text1, text1) == 1.0

    # Check empty texts
    assert calculate_semantic_overlap("", text2) == 0.0
    assert calculate_semantic_overlap(text1, None) == 0.0

def test_summarize_large_content():
    # Test short content is returned directly
    content = "Texto curto de teste"
    assert summarize_large_content(content, lambda p: "Resumo", max_chunk_size=100) == content
    
    # Test large content is chunked and summarized
    large_content = "Texto muito longo que excede o limite do chunk " * 10
    calls = []
    def mock_generate(prompt):
        calls.append(prompt)
        return "Resumo do bloco"
        
    result = summarize_large_content(large_content, mock_generate, max_chunk_size=100)
    # Check that mock_generate was called to distill chunk and consolidate
    assert len(calls) > 0
    assert "Resumo do bloco" in result

def test_get_generator_with_fallback(monkeypatch):
    import promptcraft
    
    # Mock resolve_all_api_keys to return keys for openai and gemini
    def mock_resolve_all_api_keys(provider, cli_key=None):
        if provider in ["openai", "gemini"]:
            return ["mock_key_" + provider]
        return []
        
    monkeypatch.setattr(promptcraft, "resolve_all_api_keys", mock_resolve_all_api_keys)
    
    # Mock get_generator to fail on openai but succeed on gemini
    calls = []
    def mock_get_generator(provider, model_name, api_key, temperature):
        calls.append((provider, model_name))
        if provider == "openai":
            raise Exception("OpenAI API rate limit exceeded")
        return lambda prompt: f"Response from {provider}: {prompt}"
        
    monkeypatch.setattr(promptcraft, "get_generator", mock_get_generator)
    
    # Create args mockup
    class Args:
        provider = None
        model = None
        api_key = None
        temperature = 0.7
        
    args = Args()
    generate = promptcraft.get_generator_with_fallback(args)
    
    # Assert initial attributes are set (first available provider should be openai)
    assert generate.last_provider == "openai"
    
    # Run the generator
    res = generate("Olá")
    
    # Verify fallback worked: openai failed, so gemini was tried and succeeded
    assert res == "Response from gemini: Olá"
    assert generate.last_provider == "gemini"
    assert len(calls) == 2
    assert calls[0][0] == "openai"
    assert calls[1][0] == "gemini"

def test_resolve_all_api_keys(monkeypatch):
    import promptcraft
    
    # Mock environment variables
    monkeypatch.setenv("OPENAI_API_KEY", "key1,key2")
    monkeypatch.setenv("OPENAI_API_KEY_1", "key3")
    monkeypatch.setenv("OPENAI_API_KEY_2", "key4")
    
    # Mock config
    monkeypatch.setattr(promptcraft, "load_config", lambda: {
        "openai_api_key_backup": ["key5", "key6"],
        "openai_api_key_3": "key7"
    })
    
    keys = promptcraft.resolve_all_api_keys("openai")
    expected = ["key1", "key2", "key3", "key4", "key5", "key6", "key7"]
    for k in expected:
        assert k in keys
    assert len(keys) == 7

def test_multiple_keys_fallback(monkeypatch):
    import promptcraft
    
    # Resolve all api keys returns 2 keys for openai
    monkeypatch.setattr(promptcraft, "resolve_all_api_keys", lambda prov, cli_key=None: ["key_first", "key_second"] if prov == "openai" else [])
    
    # Mock get_generator to track key and fail on first, succeed on second
    calls = []
    def mock_get_generator(provider, model_name, api_key, temperature):
        calls.append((provider, api_key))
        if api_key == "key_first":
            raise Exception("Key expired")
        return lambda prompt: f"Success with {api_key}"
        
    monkeypatch.setattr(promptcraft, "get_generator", mock_get_generator)
    
    class Args:
        provider = "openai"
        model = "gpt-4"
        api_key = None
        temperature = 0.7
        
    args = Args()
    generate = promptcraft.get_generator_with_fallback(args)
    res = generate("prompt")
    
    assert res == "Success with key_second"
    assert len(calls) == 2
    assert calls[0] == ("openai", "key_first")
    assert calls[1] == ("openai", "key_second")

