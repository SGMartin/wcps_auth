FROM python:3.12-slim

# Set environment variables
ENV database_ip=127.0.0.1
ENV database_name=auth_test
ENV database_user=root
ENV database_password=root
ENV database_port=3306
ENV server_ip=127.0.0.1


WORKDIR /app

# Install git and clean up afterwards
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Clone wcps_core, install it, and then install wcps_auth
RUN git clone https://github.com/SGMartin/wcps_core.git && \
    cd wcps_core && \
    pip install . && \
    cd .. && \
    rm -rf wcps_core


# Copy the necessary files
COPY ./wcps_auth /app/wcps_auth
COPY ./pyproject.toml /app/pyproject.toml

RUN pip install --no-cache-dir ./

RUN pip list

# Expose the necessary ports
EXPOSE 5330 5012 ${DATABASE_PORT}

CMD ["wcps-auth"]
