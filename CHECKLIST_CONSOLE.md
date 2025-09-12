# ✅ Checklist Rápido - Deploy via Console Google Cloud

## 🔧 Configuração Inicial

### 1. APIs Necessárias
- [ ] Cloud Build API
- [ ] Cloud Run API  
- [ ] Container Registry API
- [ ] Cloud Resource Manager API

**Como habilitar**: Menu ☰ > APIs e Serviços > Biblioteca > Buscar e habilitar cada uma

### 2. Conectar Repositório GitHub
- [ ] Vá para Cloud Build > Triggers
- [ ] Clique "Conectar repositório"
- [ ] Selecione GitHub
- [ ] Autorize e selecione seu repositório

## 🚀 Deploy

### 3. Criar Trigger
- [ ] Cloud Build > Triggers > Criar trigger
- [ ] Nome: `aprendizap-dashboard-trigger`
- [ ] Evento: Push para branch `master`
- [ ] Configuração: Arquivo de configuração
- [ ] Arquivo: `cloudbuild-no-git.yaml` (versão mais simples, sem Git LFS)

### 4. Configurar Variáveis
No trigger, adicione estas variáveis de substituição:
- [ ] `_REPO_NAME`: `krausz2001/aprendizap2`
- [ ] `_SERVICE_NAME`: `aprendizap-dashboard`
- [ ] `_REGION`: `us-east4`

### 5. Executar Deploy
- [ ] Faça commit e push do código
- [ ] O trigger executará automaticamente
- [ ] Monitore em Cloud Build > Histórico

## 🔍 Verificação

### 6. Verificar Build
- [ ] Cloud Build > Histórico
- [ ] Status: ✅ Sucesso
- [ ] Sem erros de Git LFS

### 7. Verificar Serviço
- [ ] Cloud Run > Serviços
- [ ] Serviço `aprendizap-dashboard` ativo
- [ ] URL funcionando

## 🐛 Problemas Comuns

### Erro: "Parquet magic bytes not found"
- [ ] Verificar se arquivos LFS estão no repositório
- [ ] Executar `git lfs pull` localmente
- [ ] Fazer commit e push novamente

### Erro: "Memory limit exceeded"
- [ ] Cloud Run > Serviços > Editar
- [ ] Aumentar memória para 4 GiB

### Erro: "Build failed"
- [ ] Verificar logs em Cloud Build > Histórico
- [ ] Confirmar se repositório está conectado
- [ ] Verificar se todas as APIs estão habilitadas

## 📞 Próximos Passos

Após deploy bem-sucedido:
1. Acesse a URL do Cloud Run
2. Teste o dashboard
3. Configure domínio personalizado (opcional)
4. Configure monitoramento (opcional)
