#!/usr/bin/env bash

set -euo pipefail

target_dir="${1:-.}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
template_file="${script_dir}/../templates/CLAUDE.md"
target_file="${target_dir}/CLAUDE.md"
managed_marker="<!-- BEGIN CLEAN CODE STANDARDS -->"
legacy_heading="# Clean Code Standards"
temporary_file=""

cleanup() {
  if [[ -n "${temporary_file}" && -f "${temporary_file}" ]]; then
    rm -f "${temporary_file}"
  fi
}

trap cleanup EXIT

if [[ ! -d "${target_dir}" ]]; then
  echo "Directory not found: ${target_dir}" >&2
  exit 1
fi

if [[ ! -f "${template_file}" ]]; then
  echo "Template not found: ${template_file}" >&2
  exit 1
fi

if [[ -f "${target_file}" ]]; then
  if grep -qF "${managed_marker}" "${target_file}"; then
    echo "Clean Code Standards are already installed in ${target_file}."
    exit 0
  fi

  if grep -qF "${legacy_heading}" "${target_file}"; then
    echo "A legacy Clean Code Standards section already exists in ${target_file}."
    echo "Review and replace that section manually to avoid overwriting project instructions."
    exit 2
  fi

  temporary_file="$(mktemp "${target_file}.tmp.XXXXXX")"
  cp -p "${target_file}" "${temporary_file}"
  printf '\n\n' >> "${temporary_file}"
  awk 'NR == 1 && $0 == "" { next } { print }' "${template_file}" >> "${temporary_file}"
  mv "${temporary_file}" "${target_file}"
  temporary_file=""
  action="Appended"
else
  temporary_file="$(mktemp "${target_file}.tmp.XXXXXX")"
  awk 'NR == 1 && $0 == "" { next } { print }' "${template_file}" > "${temporary_file}"
  mv "${temporary_file}" "${target_file}"
  temporary_file=""
  action="Created"
fi

line_count="$(wc -l < "${target_file}" | tr -d ' ')"
echo "${action} Clean Code Standards in ${target_file} (${line_count} lines)."
