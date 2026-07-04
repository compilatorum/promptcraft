(async () => {
    /* Cria container do painel de controle flutuante */
    const panel = document.createElement('div');
    panel.style.position = 'fixed';
    panel.style.top = '10px';
    panel.style.right = '10px';
    panel.style.zIndex = '999999';
    panel.style.background = '#1e1e2e';
    panel.style.color = '#cdd6f4';
    panel.style.padding = '15px';
    panel.style.borderRadius = '10px';
    panel.style.boxShadow = '0 4px 15px rgba(0,0,0,0.5)';
    panel.style.fontFamily = 'monospace';
    panel.style.maxWidth = '300px';
    panel.innerHTML = '<div style="font-weight:bold;margin-bottom:8px;color:#a6e3a1">Qwen Exporter</div><div id="qwen-status">Iniciando rolagem...</div>';
    document.body.appendChild(panel);

    const updateStatus = (text) => {
        const statusEl = document.getElementById('qwen-status');
        if (statusEl) statusEl.innerText = text;
    };

    /* 1. Rolagem Automática */
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
    let lastHeight = container === window ? document.body.scrollHeight : container.scrollHeight;
    let noChangeCount = 0;
    let steps = 0;

    while (noChangeCount < 8 && steps < 150) {
        if (container === window) {
            window.scrollTo(0, 0);
        } else {
            container.scrollTop = 0;
        }
        updateStatus(`Rolando ao topo... Passo ${steps} (Altura: ${lastHeight}px)`);
        await new Promise(r => setTimeout(r, 1500));
        
        let currentHeight = container === window ? document.body.scrollHeight : container.scrollHeight;
        if (currentHeight === lastHeight) {
            noChangeCount++;
        } else {
            noChangeCount = 0;
            lastHeight = currentHeight;
            if (container === window) window.scrollTo(0, 0); else container.scrollTop = 0;
        }
        steps++;
    }

    updateStatus("Convertendo mensagens...");

    /* 2. Conversor recursivo HTML -> Markdown */
    function convertNodeToMarkdown(node) {
        if (node.nodeType === Node.TEXT_NODE) return node.textContent;
        if (node.nodeType !== Node.ELEMENT_NODE) return "";

        const tagName = node.tagName.toLowerCase();
        if (node.classList.contains('copy-button') || 
            node.classList.contains('feedback-buttons') || 
            tagName === 'button' ||
            node.getAttribute('aria-label')?.includes('copy') ||
            ['copy', 'copiar', 'share', 'compartilhar'].includes(node.innerText?.trim().toLowerCase())) {
            return "";
        }

        let childrenMarkdown = "";
        for (const child of node.childNodes) {
            childrenMarkdown += convertNodeToMarkdown(child);
        }

        switch (tagName) {
            case 'h1': return `\n# ${childrenMarkdown.trim()}\n\n`;
            case 'h2': return `\n## ${childrenMarkdown.trim()}\n\n`;
            case 'h3': return `\n### ${childrenMarkdown.trim()}\n\n`;
            case 'h4': return `\n#### ${childrenMarkdown.trim()}\n\n`;
            case 'p': return `\n${childrenMarkdown.trim()}\n\n`;
            case 'br': return `\n`;
            case 'strong':
            case 'b': return `**${childrenMarkdown}**`;
            case 'em':
            case 'i': return `*${childrenMarkdown}*`;
            case 'code':
                if (node.parentNode && node.parentNode.tagName.toLowerCase() === 'pre') return childrenMarkdown;
                return `\`${childrenMarkdown}\``;
            case 'pre':
                let lang = "";
                const codeEl = node.querySelector('code');
                if (codeEl) {
                    for (const cls of codeEl.classList) {
                        if (cls.startsWith('language-')) { lang = cls.replace('language-', ''); break; }
                    }
                }
                const codeText = codeEl ? codeEl.innerText : node.innerText;
                return `\n\`\`\`${lang}\n${codeText.trim()}\n\`\`\`\n\n`;
            case 'li': return `- ${childrenMarkdown.trim()}\n`;
            case 'ul': return `\n${childrenMarkdown}\n`;
            case 'ol':
                let olMarkdown = "\n";
                let index = 1;
                for (const child of node.childNodes) {
                    if (child.tagName && child.tagName.toLowerCase() === 'li') {
                        olMarkdown += `${index}. ${convertNodeToMarkdown(child).trim().replace(/^- /, '')}\n`;
                        index++;
                    }
                }
                return olMarkdown + "\n";
            case 'a':
                return `[${childrenMarkdown}](${node.getAttribute('href') || ''})`;
            case 'blockquote':
                return `\n> ${childrenMarkdown.trim().replace(/\n/g, '\n> ')}\n\n`;
            default:
                return childrenMarkdown;
        }
    }

    /* 3. Extração das Mensagens */
    const assistants = Array.from(document.querySelectorAll('.markdown-body, [class*="markdown"]'));
    if (assistants.length === 0) {
        updateStatus("Erro: Não foi possível identificar mensagens do chat.");
        return;
    }

    let chatContainer = assistants[0].parentElement;
    while (chatContainer && chatContainer.tagName.toLowerCase() !== 'body') {
        if (chatContainer.querySelectorAll('.markdown-body, [class*="markdown"]').length === assistants.length) break;
        chatContainer = chatContainer.parentElement;
    }
    if (!chatContainer) chatContainer = document.body;

    const messages = [];
    const childElements = Array.from(chatContainer.children);
    for (const child of childElements) {
        const hasAssistant = child.querySelector('.markdown-body, [class*="markdown"]') || child.classList.contains('markdown-body');
        if (hasAssistant) {
            const assistantNode = child.querySelector('.markdown-body, [class*="markdown"]') || child;
            const md = convertNodeToMarkdown(assistantNode);
            if (md.trim()) messages.push({ role: 'assistant', content: md.trim() });
        } else {
            const text = child.innerText || '';
            if (text.trim().length > 0 && !child.querySelector('button') && !child.querySelector('textarea') && text.trim().length < 10000) {
                const lowerText = text.trim().toLowerCase();
                if (!['copy', 'share', 'regenerate'].includes(lowerText)) {
                    messages.push({ role: 'user', content: text.trim() });
                }
            }
        }
    }

    /* Fallback por layout se a varredura linear falhar */
    if (messages.length < assistants.length) {
        messages.length = 0;
        const chatBlocks = [];
        assistants.forEach(el => chatBlocks.push({ type: 'assistant', element: el, top: el.getBoundingClientRect().top }));
        
        const userCandidates = Array.from(chatContainer.querySelectorAll('div, p')).filter(el => {
            const rect = el.getBoundingClientRect();
            return rect.left > window.innerWidth * 0.4 && el.innerText?.trim().length > 0 && !el.querySelector('div') && !el.querySelector('button');
        });
        userCandidates.forEach(el => {
            const top = el.getBoundingClientRect().top;
            if (!chatBlocks.some(b => Math.abs(b.top - top) < 5)) chatBlocks.push({ type: 'user', element: el, top: top });
        });
        
        chatBlocks.sort((a, b) => a.top - b.top);
        chatBlocks.forEach(block => {
            if (block.type === 'assistant') {
                const md = convertNodeToMarkdown(block.element);
                if (md.trim()) messages.push({ role: 'assistant', content: md.trim() });
            } else {
                const text = block.element.innerText.trim();
                if (text && !['copy', 'share'].includes(text.toLowerCase())) {
                    if (messages.length === 0 || messages[messages.length - 1].content !== text) {
                        messages.push({ role: 'user', content: text });
                    }
                }
            }
        });
    }

    /* 4. Geração do Markdown Final */
    let mdOutput = `# Chat Qwen - ${window.location.href}\n\n`;
    messages.forEach(msg => {
        const role = msg.role === 'user' ? '👤 Usuário' : '🤖 Qwen';
        mdOutput += `### ${role}\n\n${msg.content}\n\n----------------------------------------\n\n`;
    });

    /* 5. Exibição do Modal de Cópia */
    panel.style.width = '90%';
    panel.style.maxWidth = '500px';
    panel.style.top = '10%';
    panel.style.left = '5%';
    panel.style.height = '80%';
    panel.innerHTML = `
        <div style="font-weight:bold;margin-bottom:8px;color:#a6e3a1;display:flex;justify-content:space-between;">
            <span>Qwen Exporter (Concluído)</span>
            <span id="close-exporter" style="cursor:pointer;color:#f38ba8">✕</span>
        </div>
        <textarea id="markdown-textarea" style="width:100%;height:75%;background:#313244;color:#cdd6f4;border:1px solid #45475a;border-radius:5px;padding:8px;font-family:monospace;font-size:12px;resize:none;">${mdOutput}</textarea>
        <button id="copy-markdown-btn" style="width:100%;margin-top:10px;padding:10px;background:#a6e3a1;color:#11111b;border:none;border-radius:5px;font-weight:bold;cursor:pointer;">Copiar para a Área de Transferência</button>
    `;

    document.getElementById('close-exporter').onclick = () => panel.remove();
    
    const copyBtn = document.getElementById('copy-markdown-btn');
    copyBtn.onclick = async () => {
        try {
            const textarea = document.getElementById('markdown-textarea');
            textarea.select();
            await navigator.clipboard.writeText(textarea.value);
            copyBtn.innerText = "Copiado com Sucesso!";
            copyBtn.style.background = "#94e2d5";
            setTimeout(() => {
                copyBtn.innerText = "Copiar para a Área de Transferência";
                copyBtn.style.background = "#a6e3a1";
            }, 2000);
        } catch (err) {
            try {
                document.execCommand('copy');
                copyBtn.innerText = "Copiado (Fallback)!";
            } catch(e) {
                alert("Erro ao copiar automaticamente. Selecione o texto e copie manualmente.");
            }
        }
    };
})();
