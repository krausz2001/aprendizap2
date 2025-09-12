# 1. Use uma imagem base oficial do Python
FROM python:3.10-slim

# 2. Defina o diretório de trabalho dentro do container
WORKDIR /app

# 3. Copie o arquivo de dependências e instale os pacotes
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copie todo o código do seu projeto para o diretório de trabalho
COPY . .

# 5. Diga ao Google Cloud em qual porta seu app vai rodar
# O Cloud Run envia o tráfego para a porta 8080 por padrão
ENV PORT 8080

# 6. Comando para iniciar sua aplicação
# Use a variável $PORT que o Google Cloud fornece.
# O formato ["comando", "parametro1", "parametro2"] é o preferido.
CMD ["shiny", "run", "--host", "0.0.0.0", "--port", "8080", "dash_aprendizap.py"]