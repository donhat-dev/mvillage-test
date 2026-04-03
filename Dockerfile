# syntax=docker/dockerfile:1.7

FROM odoo:18.0 AS base

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends cron logrotate \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN if [ -s /tmp/requirements.txt ]; then \
        pip3 install --no-cache-dir --break-system-packages -r /tmp/requirements.txt; \
    fi \
    && rm -f /tmp/requirements.txt

COPY docker/entrypoint.sh /entrypoint.sh
COPY config/logrotate /etc/odoo/logrotate

RUN chmod 755 /entrypoint.sh \
    && mkdir -p /var/log/odoo \
    && touch /var/log/odoo/odoo-server.log \
    && chown -R odoo:odoo /var/log/odoo /var/lib/odoo \
    && cp /etc/odoo/logrotate /etc/logrotate.d/odoo

ENTRYPOINT ["/entrypoint.sh"]
CMD ["odoo"]

FROM base AS production

FROM base AS debug

RUN pip3 install --no-cache-dir --break-system-packages debugpy
