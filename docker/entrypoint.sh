#!/bin/bash
set -e

# ----------------------------------------------------------------------
# Resolve database connection from environment variables
# ----------------------------------------------------------------------
: ${HOST:=${DB_PORT_5432_TCP_ADDR:='db'}}
: ${PORT:=${DB_PORT_5432_TCP_PORT:=5432}}
: ${USER:=${DB_ENV_POSTGRES_USER:=${POSTGRES_USER:='odoo'}}}
: ${PASSWORD:=${DB_ENV_POSTGRES_PASSWORD:=${POSTGRES_PASSWORD:='odoo'}}}

# ----------------------------------------------------------------------
# Runtime preparation
# ----------------------------------------------------------------------
prepare_runtime() {
    if [ "$(id -u)" -ne 0 ]; then
        return
    fi

    mkdir -p /var/log/odoo
    touch /var/log/odoo/odoo-server.log
    chown -R odoo:odoo /var/log/odoo /var/lib/odoo

    if command -v cron >/dev/null 2>&1; then
        cron
    fi
}

run_as_odoo() {
    if [ "$(id -u)" -eq 0 ]; then
        exec runuser -u odoo -- "$@"
    else
        exec "$@"
    fi
}

build_odoo_command() {
    ODOO_COMMAND=()

    if [ "${ODOO_ENABLE_DEBUGPY:-0}" = "1" ]; then
        ODOO_COMMAND=(python3 -Xfrozen_modules=off -m debugpy --listen 0.0.0.0:${DEBUGPY_PORT:-5678} /usr/bin/odoo)
    else
        ODOO_COMMAND=(odoo)
    fi

    ODOO_COMMAND+=("$@")
    ODOO_COMMAND+=("${DB_ARGS[@]}")
}

prepare_runtime

# ----------------------------------------------------------------------
# Build database arguments from environment / config
# ----------------------------------------------------------------------
DB_ARGS=()
function check_config() {
    param="$1"
    value="$2"
    if grep -q -E "^\s*\b${param}\b\s*=" "$ODOO_RC" ; then
        value=$(grep -E "^\s*\b${param}\b\s*=" "$ODOO_RC" | cut -d " " -f3 | sed 's/["\n\r]//g')
    fi
    DB_ARGS+=("--${param}")
    DB_ARGS+=("${value}")
}
check_config "db_host" "$HOST"
check_config "db_port" "$PORT"
check_config "db_user" "$USER"
check_config "db_password" "$PASSWORD"

# ----------------------------------------------------------------------
# Launch Odoo
# ----------------------------------------------------------------------
case "$1" in
    -- | odoo)
        shift
        if [[ "$1" == "scaffold" ]] ; then
            run_as_odoo odoo "$@"
        else
            wait-for-psql.py "${DB_ARGS[@]}" --timeout=30
            build_odoo_command "$@"
            run_as_odoo "${ODOO_COMMAND[@]}"
        fi
        ;;
    -*)
        wait-for-psql.py "${DB_ARGS[@]}" --timeout=30
        build_odoo_command "$@"
        run_as_odoo "${ODOO_COMMAND[@]}"
        ;;
    *)
        exec "$@"
esac

exit 1
