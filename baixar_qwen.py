import os
import sys
import json
import time
from playwright.sync_api import sync_playwright

def main():
    # URL do chat
    url = "https://chat.qwen.ai/c/7ca782f4-6877-4a5b-bd3c-b2f40ce971e9"
    
    print("=" * 60)
    print(" QWEN CHAT DOWNLOADER VIA CHROME DEBUG PROTOCOL (CDP)")
    print("=" * 60)
    print("Para que este script funcione:")
    print("1. Feche todas as janelas do Chrome (ou use um perfil separado).")
    print("2. Inicie o Chrome com a porta de debug habilitada:")
    print("   google-chrome --remote-debugging-port=9222 --user-data-dir=\"/tmp/chrome-debug\"")
    print("3. Faça login no Qwen se necessário e acesse o chat:")
    print(f"   {url}")
    print("4. Mantenha a aba aberta e execute este script.")
    print("-" * 60)
    
    confirm = input("O Chrome está rodando na porta 9222 com a aba do Qwen aberta? (s/n): ").strip().lower()
    if confirm != 's':
        print("Abortando. Por favor, configure o Chrome com remote debugging antes de rodar o script.")
        sys.exit(1)

    print("\nConectando ao Chrome na porta 9222...")
    try:
        with sync_playwright() as p:
            # Conecta ao Chrome existente via CDP
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            
            # Procura a aba do Qwen
            page = None
            for context in browser.contexts:
                for p_page in context.pages:
                    if "chat.qwen.ai" in p_page.url:
                        page = p_page
                        break
                if page:
                    break
            
            if not page:
                print(f"Aba do Qwen não encontrada no Chrome. Abrindo uma nova aba...")
                context = browser.contexts[0]
                page = context.new_page()
                page.goto(url)
            else:
                print(f"Aba do Qwen encontrada! URL atual: {page.url}")
                # Navega para a URL desejada se for diferente do chat específico
                if "7ca782f4-6877-4a5b-bd3c-b2f40ce971e9" not in page.url:
                    print(f"Navegando para o chat específico: {url}")
                    page.goto(url)

            print("Aguardando carregamento da página...")
            page.wait_for_timeout(3000)
            
            # Função JS para rolar até o topo e carregar mensagens anteriores
            print("Iniciando a rolagem automática até o topo para carregar o histórico...")
            js_scroll = """
            async () => {
                // Tenta encontrar o container rolável principal do chat
                function findScrollContainer() {
                    const elements = Array.from(document.querySelectorAll('*'));
                    let bestContainer = null;
                    let maxScrollHeight = 0;
                    for (const el of elements) {
                        const style = window.getComputedStyle(el);
                        if ((style.overflowY === 'auto' || style.overflowY === 'scroll') && el.scrollHeight > el.clientHeight) {
                            if (el.scrollHeight > maxScrollHeight) {
                                maxScrollHeight = el.scrollHeight;
                                bestContainer = el;
                            }
                        }
                    }
                    return bestContainer;
                }

                const container = findScrollContainer() || window;
                console.log("Container de scroll identificado:", container);

                let lastHeight = container === window ? document.body.scrollHeight : container.scrollHeight;
                let noChangeCount = 0;
                let steps = 0;

                while (noChangeCount < 8 && steps < 150) {
                    if (container === window) {
                        window.scrollTo(0, 0);
                    } else {
                        container.scrollTop = 0;
                    }
                    
                    // Espera carregar mensagens anteriores
                    await new Promise(r => setTimeout(r, 1500));
                    
                    let currentHeight = container === window ? document.body.scrollHeight : container.scrollHeight;
                    if (currentHeight === lastHeight) {
                        noChangeCount++;
                    } else {
                        noChangeCount = 0;
                        lastHeight = currentHeight;
                        if (container === window) {
                            window.scrollTo(0, 0);
                        } else {
                            container.scrollTop = 0;
                        }
                    }
                    steps++;
                }
                return steps;
            }
            """
            page.evaluate(js_scroll)
            print("Rolagem concluída! Histórico carregado.")

            # Extração de mensagens em Markdown
            print("Extraindo mensagens da página e convertendo para Markdown...")
            js_extract = """
            () => {
                // Função recursiva para converter HTML em Markdown
                function convertNodeToMarkdown(node) {
                    if (node.nodeType === Node.TEXT_NODE) {
                        return node.textContent;
                    }
                    if (node.nodeType !== Node.ELEMENT_NODE) {
                        return "";
                    }

                    const tagName = node.tagName.toLowerCase();
                    
                    // Ignora botões e controles comuns de UI
                    if (node.classList.contains('copy-button') || 
                        node.classList.contains('feedback-buttons') || 
                        tagName === 'button' ||
                        node.getAttribute('aria-label')?.includes('copy') ||
                        node.innerText === 'Copy' ||
                        node.innerText === 'Copiar' ||
                        node.innerText === 'Share' ||
                        node.innerText === 'Compartilhar') {
                        return "";
                    }

                    let childrenMarkdown = "";
                    for (const child of node.childNodes) {
                        childrenMarkdown += convertNodeToMarkdown(child);
                    }

                    switch (tagName) {
                        case 'h1': return `\\n# ${childrenMarkdown.trim()}\\n\\n`;
                        case 'h2': return `\\n## ${childrenMarkdown.trim()}\\n\\n`;
                        case 'h3': return `\\n### ${childrenMarkdown.trim()}\\n\\n`;
                        case 'h4': return `\\n#### ${childrenMarkdown.trim()}\\n\\n`;
                        case 'h5': return `\\n##### ${childrenMarkdown.trim()}\\n\\n`;
                        case 'h6': return `\\n###### ${childrenMarkdown.trim()}\\n\\n`;
                        case 'p': return `\\n${childrenMarkdown.trim()}\\n\\n`;
                        case 'br': return `\\n`;
                        case 'strong':
                        case 'b': return `**${childrenMarkdown}**`;
                        case 'em':
                        case 'i': return `*${childrenMarkdown}*`;
                        case 'code':
                            if (node.parentNode && node.parentNode.tagName.toLowerCase() === 'pre') {
                                return childrenMarkdown;
                            }
                            return `\`${childrenMarkdown}\``;
                        case 'pre':
                            let lang = "";
                            const codeEl = node.querySelector('code');
                            if (codeEl) {
                                for (const cls of codeEl.classList) {
                                    if (cls.startsWith('language-')) {
                                        lang = cls.replace('language-', '');
                                        break;
                                    }
                                }
                            }
                            const codeText = codeEl ? codeEl.innerText : node.innerText;
                            return `\\n\`\`\`${lang}\\n${codeText.trim()}\\n\`\`\`\\n\\n`;
                        case 'li': return `- ${childrenMarkdown.trim()}\\n`;
                        case 'ul': return `\\n${childrenMarkdown}\\n`;
                        case 'ol':
                            let olMarkdown = "\\n";
                            let index = 1;
                            for (const child of node.childNodes) {
                                if (child.tagName && child.tagName.toLowerCase() === 'li') {
                                    olMarkdown += `${index}. ${convertNodeToMarkdown(child).trim().replace(/^- /, '')}\\n`;
                                    index++;
                                }
                            }
                            return olMarkdown + "\\n";
                        case 'a':
                            const href = node.getAttribute('href') || '';
                            return `[${childrenMarkdown}](${href})`;
                        case 'blockquote':
                            return `\\n> ${childrenMarkdown.trim().replace(/\\n/g, '\\n> ')}\\n\\n`;
                        default:
                            return childrenMarkdown;
                    }
                }

                // Identifica os blocos de mensagens na página
                const assistants = Array.from(document.querySelectorAll('.markdown-body, [class*="markdown"]'));
                if (assistants.length === 0) {
                    return [{ role: 'system', content: 'Não foi possível encontrar blocos de mensagens do Qwen (classe .markdown-body ausente).' }];
                }

                // Encontra o container comum que abriga as mensagens do chat
                let chatContainer = assistants[0].parentElement;
                while (chatContainer && chatContainer.tagName.toLowerCase() !== 'body') {
                    const contained = chatContainer.querySelectorAll('.markdown-body, [class*="markdown"]');
                    if (contained.length === assistants.length) {
                        break;
                    }
                    chatContainer = chatContainer.parentElement;
                }
                
                if (!chatContainer) chatContainer = document.body;

                const messages = [];
                
                // Tenta extrair a partir dos filhos diretos do chatContainer
                const childElements = Array.from(chatContainer.children);
                for (const child of childElements) {
                    const hasAssistant = child.querySelector('.markdown-body, [class*="markdown"]') || child.classList.contains('markdown-body');
                    
                    if (hasAssistant) {
                        const assistantNode = child.querySelector('.markdown-body, [class*="markdown"]') || child;
                        const md = convertNodeToMarkdown(assistantNode);
                        if (md.trim()) {
                            messages.push({ role: 'assistant', content: md.trim() });
                        }
                    } else {
                        const text = child.innerText || '';
                        if (text.trim().length > 0 && 
                            !child.querySelector('button') && 
                            !child.querySelector('textarea') && 
                            text.trim().length < 10000) {
                            
                            const lowerText = text.trim().toLowerCase();
                            if (lowerText !== 'copy' && lowerText !== 'share' && lowerText !== 'regenerate') {
                                messages.push({ role: 'user', content: text.trim() });
                            }
                        }
                    }
                }

                // Fallback heurístico baseado no layout e ordenação vertical
                if (messages.length < assistants.length) {
                    const fallbackMessages = [];
                    const chatBlocks = [];
                    
                    assistants.forEach(el => {
                        chatBlocks.push({ type: 'assistant', element: el, top: el.getBoundingClientRect().top });
                    });
                    
                    const userCandidates = Array.from(chatContainer.querySelectorAll('div, p')).filter(el => {
                        const rect = el.getBoundingClientRect();
                        const isRight = rect.left > window.innerWidth * 0.4;
                        const hasText = el.innerText && el.innerText.trim().length > 0 && el.innerText.trim().length < 5000;
                        const isLeaf = !el.querySelector('div');
                        const notControl = !el.querySelector('button') && !el.querySelector('textarea');
                        
                        return isRight && hasText && isLeaf && notControl;
                    });
                    
                    userCandidates.forEach(el => {
                        const top = el.getBoundingClientRect().top;
                        if (!chatBlocks.some(b => Math.abs(b.top - top) < 5)) {
                            chatBlocks.push({ type: 'user', element: el, top: top });
                        }
                    });
                    
                    chatBlocks.sort((a, b) => a.top - b.top);
                    
                    chatBlocks.forEach(block => {
                        if (block.type === 'assistant') {
                            const md = convertNodeToMarkdown(block.element);
                            if (md.trim()) {
                                fallbackMessages.push({ role: 'assistant', content: md.trim() });
                            }
                        } else {
                            const text = block.element.innerText.trim();
                            if (text && text.length > 1 && text.toLowerCase() !== 'copy' && text.toLowerCase() !== 'share') {
                                if (fallbackMessages.length === 0 || fallbackMessages[fallbackMessages.length - 1].content !== text) {
                                    fallbackMessages.push({ role: 'user', content: text });
                                }
                            }
                        }
                    });
                    
                    if (fallbackMessages.length >= assistants.length) {
                        return fallbackMessages;
                    }
                }

                return messages;
            }
            """
            
            messages = page.evaluate(js_extract)
            
            if not messages or (len(messages) == 1 and messages[0]['role'] == 'system'):
                print("Aviso: A extração heurística automática não encontrou mensagens ou falhou.")
                print("Salvando o HTML bruto da página para depuração...")
                html_content = page.content()
                with open("qwen_raw_page.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print("HTML bruto salvo em 'qwen_raw_page.html'.")
                return

            print(f"Extraídas {len(messages)} mensagens com sucesso!")
            
            # Formatação do Markdown
            md_content = []
            md_content.append(f"# Chat Qwen - {url}\n")
            md_content.append(f"Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            md_content.append("-" * 40 + "\n\n")
            
            for msg in messages:
                role = msg.get('role', 'unknown').capitalize()
                content = msg.get('content', '')
                if role == 'User':
                    md_content.append(f"### 👤 Usuário\n\n{content}\n\n")
                elif role == 'Assistant':
                    md_content.append(f"### 🤖 Qwen\n\n{content}\n\n")
                else:
                    md_content.append(f"### ⚙️ {role}\n\n{content}\n\n")
                md_content.append("-" * 40 + "\n\n")
            
            filename = "qwen_chatlog_7ca782f4.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("".join(md_content))
            
            print(f"Sucesso! Chatlog salvo em: {os.path.abspath(filename)}")
            print(f"Tamanho do arquivo: {os.path.getsize(filename)} bytes")
            
    except Exception as e:
        print(f"\nErro ao conectar ou automatizar o Chrome: {e}")
        print("Certifique-se de que o Chrome está rodando com '--remote-debugging-port=9222' e que o perfil de usuário foi especificado.")

if __name__ == "__main__":
    main()
