#!/usr/bin/env bash
set -euo pipefail

add_rule() {
  local bin="$1"
  local iface="$2"

  command -v "$bin" >/dev/null 2>&1 || return 0
  [ -n "$iface" ] || return 0

  "$bin" -N DOCKER-USER 2>/dev/null || true
  "$bin" -C DOCKER-USER -i "$iface" -p tcp --dport 5432 -j DROP 2>/dev/null \
    || "$bin" -I DOCKER-USER 1 -i "$iface" -p tcp --dport 5432 -j DROP
}

iface4="$(ip -o -4 route show default 2>/dev/null | awk '{print $5; exit}')"
iface6="$(ip -o -6 route show default 2>/dev/null | awk '{print $5; exit}')"

add_rule iptables "$iface4"
add_rule ip6tables "$iface6"

echo "Postgres Docker port 5432 is blocked on public interfaces: ${iface4:-none} ${iface6:-none}"
