#!/usr/bin/env bash
#
# Install or update the Clean Code Standards block in a project's CLAUDE.md.
#
#   add-clean-code.sh [target-dir] [--update] [--check]
#
# The block is delimited by BEGIN/END markers and carries a version, so an
# installed copy can be compared with the shipped one. Without that, a
# correction shipped in a later release could never reach anyone who had
# already installed, which is exactly what happened between v3.1.0 and v3.2.1.
#
#   (no flag)  install if absent; if present but out of date, say so and exit 3
#   --check    report only, change nothing (exit 3 if an update is available)
#   --update   replace the managed block in place, leaving everything else alone

set -euo pipefail

target_dir="."
mode="install"
for arg in "$@"; do
  case "${arg}" in
    --update) mode="update" ;;
    --check)  mode="check" ;;
    --*) echo "Unknown option: ${arg}" >&2; exit 64 ;;
    *) target_dir="${arg}" ;;
  esac
done

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
template_file="${script_dir}/../templates/CLAUDE.md"
target_file="${target_dir}/CLAUDE.md"
begin_prefix="<!-- BEGIN CLEAN CODE STANDARDS"
end_marker="<!-- END CLEAN CODE STANDARDS -->"
legacy_heading="# Clean Code Standards"
temporary_file=""

cleanup() { [[ -n "${temporary_file}" && -f "${temporary_file}" ]] && rm -f "${temporary_file}"; return 0; }
trap cleanup EXIT

[[ -d "${target_dir}" ]]   || { echo "Directory not found: ${target_dir}" >&2; exit 1; }
[[ -f "${template_file}" ]] || { echo "Template not found: ${template_file}" >&2; exit 1; }

shipped_version="$(grep -m1 -o "${begin_prefix}[^>]*" "${template_file}" | sed "s|${begin_prefix} *||; s| *-*$||")"
shipped_version="${shipped_version:-unversioned}"

write_atomically() {  # $1 = content-producing command writing to stdout
  temporary_file="$(mktemp "${target_file}.tmp.XXXXXX")"
  "$@" > "${temporary_file}"
  mv "${temporary_file}" "${target_file}"
  temporary_file=""
}

strip_leading_blank() { awk 'NR == 1 && $0 == "" { next } { print }' "${template_file}"; }

if [[ -f "${target_file}" ]]; then
  if grep -qF "${begin_prefix}" "${target_file}"; then
    installed_version="$(grep -m1 -o "${begin_prefix}[^>]*" "${target_file}" | sed "s|${begin_prefix} *||; s| *-*$||")"
    installed_version="${installed_version:-unversioned}"

    if [[ "${installed_version}" == "${shipped_version}" ]] && \
       diff -q <(sed -n "/${begin_prefix}/,/${end_marker}/p" "${target_file}") \
               <(sed -n "/${begin_prefix}/,/${end_marker}/p" "${template_file}") >/dev/null; then
      echo "Clean Code Standards are up to date in ${target_file} (${installed_version})."
      exit 0
    fi

    if [[ "${mode}" != "update" ]]; then
      echo "An update is available for ${target_file}."
      echo "  installed: ${installed_version}"
      echo "  shipped:   ${shipped_version}"
      echo "What would change inside the managed block:"
      diff <(sed -n "/${begin_prefix}/,/${end_marker}/p" "${target_file}") \
           <(sed -n "/${begin_prefix}/,/${end_marker}/p" "${template_file}") || true
      echo "Re-run with --update to replace the managed block. Nothing outside it is touched."
      exit 3
    fi

    if ! grep -qF "${end_marker}" "${target_file}"; then
      echo "The managed block in ${target_file} has no END marker, so its boundary is unclear." >&2
      echo "Fix it by hand rather than risk overwriting your own instructions." >&2
      exit 2
    fi

    write_atomically awk -v begin="${begin_prefix}" -v endm="${end_marker}" -v tpl="${template_file}" '
      index($0, begin) == 1 { inblock = 1; while ((getline line < tpl) > 0) print line; close(tpl); next }
      inblock && index($0, endm) == 1 { inblock = 0; next }
      !inblock { print }
    ' "${target_file}"
    echo "Updated Clean Code Standards in ${target_file} (${installed_version} -> ${shipped_version})."
    exit 0
  fi

  if grep -qF "${legacy_heading}" "${target_file}"; then
    echo "A legacy Clean Code Standards section already exists in ${target_file}."
    echo "Review and replace that section manually to avoid overwriting project instructions."
    exit 2
  fi

  [[ "${mode}" == "check" ]] && { echo "Not installed in ${target_file}."; exit 3; }

  temporary_file="$(mktemp "${target_file}.tmp.XXXXXX")"
  cp -p "${target_file}" "${temporary_file}"
  printf '\n\n' >> "${temporary_file}"
  strip_leading_blank >> "${temporary_file}"
  mv "${temporary_file}" "${target_file}"
  temporary_file=""
  action="Appended"
else
  [[ "${mode}" == "check" ]] && { echo "No CLAUDE.md in ${target_dir}."; exit 3; }
  write_atomically strip_leading_blank
  action="Created"
fi

echo "${action} Clean Code Standards in ${target_file} (${shipped_version}, $(wc -l < "${target_file}" | tr -d ' ') lines)."
