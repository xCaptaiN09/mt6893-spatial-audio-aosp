# Publish this preview

These commands are for the maintainer's **fish** shell on Arch Linux. They create
a **public** GitHub repository and a **prerelease** after the local package is
checked. The handoff itself does not publish anything.

## Extract and verify

Save `mt6893-spatial-audio-aosp-repository-v0.1.3-preview.zip` in Downloads.

```fish
mkdir -p ~/Projects
and test ! -e ~/Projects/mt6893-spatial-audio-aosp
and unzip -n ~/Downloads/mt6893-spatial-audio-aosp-repository-v0.1.3-preview.zip -d ~/Projects
and cd ~/Projects/mt6893-spatial-audio-aosp
and python3 tools/build.py
and python3 tools/check.py
```

If that project directory already exists, stop and inspect it before extracting.
The command deliberately refuses to merge the handoff into an existing folder.
The ready-made module ZIP and checksum are in `dist/`; rebuilding them requires
Python only. Do not install the repository ZIP as a module.

## Create and push the repository

GitHub CLI (`gh`) must already be signed in as `xCaptaiN09`. Check with
`gh auth status`. If login is required, use `gh auth login` before continuing.

```fish
git init -b main
and git config user.name 'xCaptaiN09'
and git config user.email '116649374+xCaptaiN09@users.noreply.github.com'
and git add .
and git diff --cached --check
and git commit -m 'Publish MT6893 Spatial Audio AOSP preview'
and gh repo create xCaptaiN09/mt6893-spatial-audio-aosp --public --source=. --remote=origin --description 'Oplus Spatial Audio compatibility preview for the inspected RMX3031 Evolution X AOSP build' --push
```

`dist/` and `build/` are ignored by Git. The repository contains the clean runtime
payload, project source, tests and notices; generated ZIPs are release assets.
No raw phone logs, APKs, media downloads or old workspaces are included.

## Tag and create the prerelease

```fish
git tag -a v0.1.3-preview -m 'MT6893 Spatial Audio AOSP v0.1.3-preview'
and git push origin v0.1.3-preview
and gh release create v0.1.3-preview dist/MT6893-Spatial-Audio-AOSP-v0.1.3-preview.zip dist/MT6893-Spatial-Audio-AOSP-v0.1.3-preview.zip.sha256 --verify-tag --prerelease --latest=false --title 'MT6893 Spatial Audio AOSP v0.1.3-preview' --notes-file docs/releases/v0.1.3-preview.md
```

Expected repository URL after creation:
https://github.com/xCaptaiN09/mt6893-spatial-audio-aosp

The release remains a preview. Once fixes are implemented and tested, increase
the version and versionCode, write new release notes and publish a new tag/asset.
Do not silently replace this preview's binaries with an unrelated fix build.

Reference: [gh repo create](https://cli.github.com/manual/gh_repo_create),
[gh release create](https://cli.github.com/manual/gh_release_create).
