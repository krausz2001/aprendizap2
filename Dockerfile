# 1. Use uma imagem base oficial do Python
FROM python:3.10-slim

# 2. Instalar dependências do sistema necessárias para matplotlib, pyarrow e git
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libc6-dev \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

# 3. Configurar Git LFS
RUN git lfs install

# 4. Defina o diretório de trabalho dentro do container
WORKDIR /app

# 5. Copie o arquivo de dependências e instale os pacotes Python
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 6. Copie todo o código do seu projeto para o diretório de trabalho
COPY . .

# 7. Baixar arquivos LFS após copiar o código
RUN git lfs pull

# 8. Criar diretório para dados se não existir
RUN mkdir -p Dados Data

# 9. Configurar variáveis de ambiente
ENV PORT=8080
ENV PYTHONPATH=/app
ENV MPLBACKEND=Agg

# 10. Expor a porta
EXPOSE 8080

# 11. Comando para iniciar sua aplicação
# Use a variável $PORT que o Google Cloud fornece
CMD ["python", "-m", "shiny", "run", "--host", "0.0.0.0", "--port", "8080", "dash_aprendizap.py"]