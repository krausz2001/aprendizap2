# 🚀 Guia de Deploy - AprendiZAP Dashboard no Google Cloud Console

## 📋 Pré-requisitos
- Conta Google Cloud ativa
- Projeto criado no Google Cloud
- Repositório GitHub com o código

## 🔧 Passo 1: Configurar Cloud Build

### 1.1 Acessar Cloud Build
1. No Console do Google Cloud, vá para **Cloud Build** > **Triggers**
2. Clique em **"Criar trigger"**

### 1.2 Configurar o Trigger
- **Nome**: `aprendizap-dashboard-trigger`
- **Fonte do evento**: `Push para um branch`
- **Repositório**: Conecte seu repositório GitHub
- **Branch**: `master` (ou sua branch principal)
- **Configuração**: `Arquivo de configuração do Cloud Build`
- **Localização**: `/cloudbuild.yaml`

### 1.3 Configurações Avançadas
- **Variáveis de substituição**:
  - `_REPO_NAME`: `seu-usuario/seu-repositorio`
  - `_SERVICE_NAME`: `aprendizap-dashboard`
  - `_REGION`: `us-east4`

## 🏗️ Passo 2: Configurar Cloud Run

### 2.1 Acessar Cloud Run
1. Vá para **Cloud Run** no menu lateral
2. Clique em **"Criar serviço"**

### 2.2 Configurações do Serviço
- **Nome do serviço**: `aprendizap-dashboard`
- **Região**: `us-east4`
- **Permitir tráfego não autenticado**: ✅ **Marcado**

### 2.3 Configurações de Container
- **Imagem do container**: Será preenchida automaticamente após o build
- **Porta**: `8080`
- **Variáveis de ambiente**:
  - `PORT`: `8080`
  - `PYTHONPATH`: `/app`
  - `MPLBACKEND`: `Agg`

### 2.4 Recursos e Limites
- **CPU**: `2`
- **Memória**: `2 GiB`
- **Timeout da solicitação**: `300 segundos`
- **Máximo de instâncias**: `10`

## 🔄 Passo 3: Executar o Deploy

### 3.1 Fazer Push do Código
1. Faça commit e push do código para o GitHub
2. O trigger do Cloud Build será executado automaticamente

### 3.2 Monitorar o Build
1. Vá para **Cloud Build** > **Histórico**
2. Acompanhe o progresso do build
3. Verifique se não há erros

### 3.3 Verificar o Deploy
1. Vá para **Cloud Run** > **Serviços**
2. Verifique se o serviço `aprendizap-dashboard` está ativo
3. Clique no serviço para ver a URL

## 🐛 Solução de Problemas

### Problema: Erro de Git LFS
**Solução**: O `cloudbuild.yaml` já está configurado para baixar arquivos LFS

### Problema: Arquivos parquet corrompidos
**Solução**: 
1. Verifique se os arquivos estão no repositório
2. Execute `git lfs pull` localmente
3. Faça commit e push novamente

### Problema: Memória insuficiente
**Solução**: 
1. Vá para Cloud Run > Serviços
2. Clique no serviço
3. Edite e aumente a memória para 4 GiB

## 📊 Monitoramento

### Logs
1. **Cloud Run** > **Serviços** > `aprendizap-dashboard`
2. Aba **"Logs"** para ver logs em tempo real

### Métricas
1. Aba **"Métricas"** para ver performance
2. Monitore CPU, memória e requisições

## 🔄 Atualizações

Para atualizar o dashboard:
1. Faça alterações no código
2. Commit e push para GitHub
3. O Cloud Build executará automaticamente
4. O Cloud Run será atualizado automaticamente

## 🌐 Acesso ao Dashboard

Após o deploy bem-sucedido:
1. Vá para **Cloud Run** > **Serviços**
2. Clique em `aprendizap-dashboard`
3. Copie a URL fornecida
4. Acesse no navegador

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs do Cloud Build
2. Verifique os logs do Cloud Run
3. Confirme se todas as APIs estão habilitadas
4. Verifique se o repositório está conectado corretamente
