#!/usr/bin/env fish

if test (count $argv) -lt 1
    echo "Usage: run_all.fish <dir> [analyze-args...]" >&2
    exit 1
end

set dir $argv[1]
set analyze_args $argv[2..]

set entries (curl -s https://reservoir.lean-lang.org/index/manifest.json | jq '.packages[]|{owner,name,gitUrl:.sources[0].gitUrl}' -c)
set total (count $entries)
set i 0

for entry in $entries
    set i (math $i + 1)
    set owner (echo $entry | jq -r '.owner')
    set name (echo $entry | jq -r '.name')
    set git_url (echo $entry | jq -r '.gitUrl')

    set repo_dir $dir/$owner/$name
    set result_file $dir/$owner/$name.json

    echo
    set_color --bold cyan
    echo "=== $owner/$name ($i/$total) ==="
    set_color normal

    mkdir -p $dir/$owner
    uv run impeller-analyze $repo_dir -u $git_url $analyze_args
end
