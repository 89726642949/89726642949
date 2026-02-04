# Sistema de Atividades (Windows Desktop)

Aplicativo desktop local para organizar e contabilizar atividades por categorias, com relatorios mensais e anuais.

## Tecnologia escolhida (justificativa)
**Python + PySide6 (Qt) + SQLite**:
- Estavel e leve para uso diario em Windows.
- Funciona totalmente offline com dados locais.
- Interface rica (dashboard, tabelas, dialogos) e facil de empacotar em exe.

---

## Estrutura de pastas
```
app/
  main.py
  assets/
    style.qss
  services/
    auth.py
    backup.py
    db.py
    records.py
    reports.py
    sample_data.py
    utils.py
  ui/
    login_dialog.py
    main_window.py
    record_dialog.py
    report_dialogs.py
    settings_dialog.py
data/              # banco SQLite (criado em runtime)
attachments/       # anexos copiados
reports/           # relatorios PDF/XLSX
logs/              # log de erros
requirements.txt
```

---

## Instalacao no Windows (passo a passo)

### 1) Instalar o Python
1. Baixe o Python 3.11+ em: https://www.python.org/downloads/
2. Durante a instalacao, marque **"Add python.exe to PATH"**.

### 2) Baixar o projeto
1. Copie esta pasta para um local do seu PC (ex.: `C:\SistemaAtividades`).

### 3) Criar ambiente virtual e instalar dependencias
Abra o **Prompt de Comando** e rode:
```
cd C:\SistemaAtividades
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 4) Executar o sistema
```
python -m app.main
```
Na primeira abertura, o sistema vai pedir para criar a senha.

---

## Criar atalho na area de trabalho
1. Abra o Bloco de Notas e cole:
```
@echo off
cd /d C:\SistemaAtividades
call .venv\Scripts\activate
python -m app.main
```
2. Salve como `SistemaAtividades.bat`.
3. Clique com o botao direito > **Criar atalho** e mova para a area de trabalho.

---

## Backup e Restore
- **Backup**: clique em **Backup** e salve o arquivo `.zip` em local seguro.
- **Restore**: clique em **Restore** e selecione o `.zip`. Isso substitui os dados atuais.

---

## Gerar relatorios
- **Relatorio Mensal**: selecione mes/ano e gere PDF e Excel.
- **Relatorio Anual**: selecione o ano e gere PDF e Excel.
- Os arquivos ficam na pasta `reports/`.

---

## Atualizar o app no futuro sem perder dados
1. Faca **Backup** antes.
2. Substitua apenas a pasta `app/` e os arquivos `.py`.
3. Nao apague as pastas `data/`, `attachments/`, `reports/`.
4. Abra o sistema normalmente.

---

## Checklist de testes (verificacao rapida)
1. **Login**: criar senha e entrar com sucesso.
2. **Auto-bloqueio**: esperar o tempo definido e desbloquear com senha.
3. **CRUD**: criar, editar, duplicar e excluir registros.
4. **Duplicidade**: salvar registro similar e ver aviso (permitir salvar).
5. **Filtros**: buscar por numero, assunto, data, categoria, status, tags.
6. **Ordenacao**: ordenar por data e numero.
7. **Backup/Restore**: gerar zip e restaurar.
8. **Relatorios**: gerar mensal e anual (PDF e Excel).
9. **Exportar lista**: exportar registros filtrados para Excel.
10. **Anexos**: anexar arquivo e ver o caminho salvo.

---

## Observacoes importantes
- Dados locais no arquivo `data/app.db`.
- Logs simples em `logs/app.log`.
- O sistema ja vem com **10 registros ficticios** na primeira execucao, para exemplo.
- Para zerar o exemplo, apague `data/app.db` e abra novamente.

