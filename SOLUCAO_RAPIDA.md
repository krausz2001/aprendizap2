# 🚀 Solução Rápida - Deploy AprendiZAP Dashboard

## ❌ **Problema atual:**
- Erro no Git LFS durante o build
- Container não consegue iniciar

## ✅ **Solução:**

### 1. **Atualizar o trigger no Console Google Cloud:**

1. Vá para **Cloud Build** > **Triggers**
2. Clique no trigger existente
3. Edite as configurações:
   - **Arquivo de configuração**: `/cloudbuild-no-git.yaml`
   - **Variáveis de substituição**:
     - `_REPO_NAME`: `krausz2001/aprendizap2`
     - `_SERVICE_NAME`: `aprendizap-dashboard`
     - `_REGION`: `us-east4`

### 2. **Fazer commit e push dos novos arquivos:**

```bash
git add .
git commit -m "Add simplified build configuration"
git push
```

### 3. **Verificar o build:**

1. Vá para **Cloud Build** > **Histórico**
2. Acompanhe o progresso do build
3. Deve funcionar agora sem erros de Git LFS

## 📁 **Arquivos importantes:**

- ✅ `cloudbuild-no-git.yaml` - Configuração simplificada
- ✅ `Dockerfile.demo` - Dockerfile otimizado
- ✅ `dash_aprendizap_demo.py` - Dashboard funcional
- ✅ `requirements.txt` - Dependências

## 🎯 **Resultado esperado:**

- ✅ Build bem-sucedido
- ✅ Deploy no Cloud Run funcionando
- ✅ Dashboard acessível via URL
- ✅ Dados de demonstração funcionando

## 🔧 **Se ainda der erro:**

1. Verifique se todos os arquivos estão no repositório
2. Confirme se as variáveis estão corretas
3. Verifique os logs do Cloud Build para detalhes

## 📞 **Próximos passos:**

Após o deploy bem-sucedido:
1. Acesse a URL do Cloud Run
2. Teste o dashboard
3. Configure domínio personalizado (opcional)
