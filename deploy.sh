#!/bin/bash

# Script para deploy no Google Cloud Run
# Execute: chmod +x deploy.sh && ./deploy.sh

# Configurações
PROJECT_ID="seu-project-id"  # Substitua pelo seu Project ID
SERVICE_NAME="aprendizap-dashboard"
REGION="us-east4"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "🚀 Iniciando deploy do AprendiZAP Dashboard..."

# 1. Configurar projeto
echo "📋 Configurando projeto..."
gcloud config set project $PROJECT_ID

# 2. Habilitar APIs necessárias
echo "🔧 Habilitando APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# 3. Fazer build da imagem
echo "🏗️ Fazendo build da imagem Docker..."
gcloud builds submit --tag $IMAGE_NAME .

# 4. Deploy no Cloud Run
echo "🚀 Fazendo deploy no Cloud Run..."
gcloud run deploy $SERVICE_NAME \
  --image $IMAGE_NAME \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --max-instances 10

echo "✅ Deploy concluído!"
echo "🌐 URL do serviço:"
gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format 'value(status.url)'
