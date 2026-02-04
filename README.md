# Sistema de Atividades (Windows / Desktop)

Aplicativo local para organizar e contabilizar atividades por categorias, com
relatorios mensais e anuais. Dados ficam no PC em SQLite, com login e backup.

## Escolha de tecnologia
- **Python + PySide6 + SQLite**: interface nativa, leve e estavel no Windows,
  facil de instalar/empacotar e sem dependencia de internet.

---

## Estrutura de pastas do projeto

```
/
├─ sistema_atividades/
│  ├─ __init__.py
│  ├─ __main__.py
│  ├─ app.py
│  ├─ constants.py
│  ├─ db.py
│  ├─ logging_config.py
│  ├─ paths.py
│  ├─ security.py
│  ├─ services/
│  │  ├─ backup_service.py
│  │  ├─ export_service.py
│  │  └─ report_service.py
│  └─ ui/
│     ├─ dashboard.py
│     ├─ dialogs.py
│     ├─ main_window.py
│     └─ records_page.py
├─ requirements.txt
└─ README.md
```

> Os dados do usuario sao gravados em:
> **%APPDATA%\\SistemaAtividades\\data** (SQLite e anexos)

---

## Instalacao no Windows (passo a passo)

### 1) Instale o Python
Baixe e instale o **Python 3.11 ou 3.12**:
- https://www.python.org/downloads/windows/
- Marque a opcao **"Add Python to PATH"** durante a instalacao.

### 2) Abra o terminal (Prompt de Comando ou PowerShell)
Navegue ate a pasta do projeto:
```
cd C:\caminho\para\o\projeto
```

### 3) Crie e ative o ambiente virtual
```
python -m venv .venv
.venv\Scripts\activate
```

### 4) Instale dependencias
```
pip install -r requirements.txt
```

### 5) Execute o aplicativo
```
python -m sistema_atividades
```

Na primeira vez:
- Defina a senha
- O sistema cria 10 registros ficticios de exemplo

---

## Criar atalho na area de trabalho

1) Crie um arquivo `SistemaAtividades.bat` em qualquer lugar, com:
```
@echo off
cd C:\caminho\para\o\projeto
call .venv\Scripts\activate
python -m sistema_atividades
```

2) Clique com o botao direito no arquivo `.bat` e escolha **Enviar para > Area de trabalho**.

> Dica: para nao abrir o terminal, voce pode usar `pythonw`:
> `pythonw -m sistema_atividades`

---

## Como usar (rotina diaria)

1. Clique em **Novo Registro**
2. Preencha os campos e salve
3. Use a **Busca global** e filtros para localizar rapidamente
4. Use **Duplicar** quando for reaproveitar um cadastro

---

## Backup e Restore

### Backup
1. Clique em **Backup**
2. Escolha onde salvar o arquivo `.zip`

### Restore
1. Clique em **Restaurar**
2. Selecione o arquivo `.zip`
3. Reinicie o aplicativo

---

## Relatorios

### Relatorio Mensal
1. Clique em **Relatorio Mensal**
2. Selecione mes/ano e pasta de saida
3. O sistema gera **PDF** e **Excel**

### Relatorio Anual
1. Clique em **Relatorio Anual**
2. Selecione o ano e pasta de saida
3. O sistema gera **PDF** e **Excel**

---

## Checklist de testes (validacao)

- [ ] Criar registro com campos obrigatorios
- [ ] Editar registro e salvar
- [ ] Duplicar registro
- [ ] Excluir registro com confirmacao
- [ ] Buscar por numero, nome, assunto e data
- [ ] Filtrar por categoria, status, tags e periodo
- [ ] Ver totais no dashboard
- [ ] Gerar relatorio mensal (PDF e XLSX)
- [ ] Gerar relatorio anual (PDF e XLSX)
- [ ] Exportar lista filtrada para Excel
- [ ] Criar backup e restaurar
- [ ] Auto-bloqueio por inatividade

---

## Qualidade e confiabilidade

- **Erros tratados** com mensagens amigaveis
- **Logs simples** em `%APPDATA%\SistemaAtividades\logs\app.log`
- **Sem travamentos**: operacoes pesadas sao locais e simples

### Atualizar o app sem perder dados
Os dados ficam fora do codigo, em:
```
%APPDATA%\SistemaAtividades\data\app.db
```
Assim, voce pode:
1. Fazer backup
2. Atualizar o codigo do projeto
3. Manter o banco intacto

---

## Observacoes
- O app funciona 100% offline
- Dados ficam locais, com senha e hash seguro
