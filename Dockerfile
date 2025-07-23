# Use official lightweight Python image
FROM python:3.10-slim

# Set working directory inside the container
WORKDIR /app

# Copy dependency file and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL source code into the container
COPY . .

# Expose Streamlit's default port
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.enableCORS=false"]
