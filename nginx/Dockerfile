FROM nginx:1.25.4-alpine

# Удаляем дефолтную конфигурацию
RUN rm /etc/nginx/conf.d/default.conf

# Копируем нашу конфигурацию
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN mkdir -p /app/static && \
    mkdir -p /app/media && \
    chown -R nginx:nginx /app && \
    chmod -R 755 /app

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
