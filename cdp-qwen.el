;;; cdp-qwen.el --- Importar conversas do Qwen via CDP para o Emacs -*- lexical-binding: t; -*-

;; Este arquivo fornece comandos para integrar o download de chatlogs
;; do Qwen via Chrome DevTools Protocol diretamente no Emacs.

(defcustom qwen-downloader-script-path "/home/sukata/promptcraft/baixar_qwen.py"
  "Caminho para o script Python de download do Qwen."
  :type 'file
  :group 'qwen)

;;;###autoload
(defun qwen-download-chat ()
  "Executa o script Python para baixar o chat do Qwen via CDP e abre o resultado no Emacs.
Certifique-se de que o Chrome Android ou Desktop esteja aberto com remote debugging na porta 9222."
  (interactive)
  (let* ((default-directory (file-name-directory qwen-downloader-script-path))
         (output-buffer (get-buffer-create "*Qwen Downloader Output*"))
         (target-file (expand-file-name "qwen_chatlog_7ca782f4.md" default-directory)))
    
    (message "Conectando ao Chrome (CDP) e iniciando extração...")
    (display-buffer output-buffer)
    
    ;; Executa o script de forma assíncrona
    (let ((process (start-process "qwen-downloader" output-buffer
                                  "python3" qwen-downloader-script-path)))
      
      ;; Envia automaticamente "s" para responder ao input de confirmação do script
      (process-send-string process "s\n")
      
      (set-process-sentinel
       process
       (lambda (proc event)
         (cond
          ((string-match-p "finished" event)
           (message "Extração do Qwen concluída com sucesso!")
           (if (file-exists-p target-file)
               (let ((buf (find-file-noselect target-file)))
                 (with-current-buffer buf
                   (when (fboundp 'markdown-mode)
                     (markdown-mode)))
                 (switch-to-buffer buf))
             (message "Aviso: Arquivo Markdown não encontrado. Verifique o buffer %s para detalhes." (buffer-name output-buffer))))
          
          ((string-match-p "aborted\\|exited\\|failed" event)
           (message "Erro na execução do downloader. Verifique o buffer %s." (buffer-name output-buffer)))))))))

(provide 'cdp-qwen)
;;; cdp-qwen.el ends here
