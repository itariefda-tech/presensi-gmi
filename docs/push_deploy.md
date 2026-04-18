# Push Deploy (Serial + Manual)

Alur ini memakai GitHub sebagai sumber utama, lalu update VPS secara manual.
Dokumen ini hanya berlaku untuk workflow VPS saat ini. Referensi stack hosting lama dan contoh topologi lama sudah dipensiunkan dari repo.

## 1) Windows (VS Code / PowerShell)

```powershell
git add .
git commit -m "update ..."
git push origin main
```

## 2) VPS (manual deploy)

```bash
ssh <user>@<vps-host>
cd /opt/presensi-app
git pull origin main
./deploy.sh
```

## Opsional: manual tanpa skrip deploy

```bash
ssh <user>@<vps-host>
cd /opt/presensi-app
git pull origin main
docker build -t presensi-app:latest .
docker stop presensi-app && docker rm presensi-app
docker run -d --name presensi-app \
  --restart unless-stopped \
  -p 5050:5050 \
  --env-file /opt/presensi-app/.env \
  -e PRESENSI_DB_PATH=/data/presensi.db \
  -v /opt/presensi-app/data:/data \
  presensi-app:latest
```

Catatan:
- Simpan seluruh secret produksi di `.env` pada VPS, bukan di repo.
- Jika VPS memakai reverse proxy atau tunnel, sambungkan service sesuai stack aktif di server, bukan dari contoh lama repo ini.

## Ringkas (harian)

1) Windows:

```powershell
git add .
git commit -m "update ..."
git push origin main
```

2) VPS:

```bash
ssh <user>@<vps-host>
cd /opt/presensi-app
./deploy.sh
```

## Prompt template (project lain)

Gunakan template ini untuk minta setup deploy di project lain:

```
Saya mau setup workflow deploy manual serial:
- Coding di Windows (VS Code) -> push ke GitHub
- Di VPS (Linux) -> git pull -> docker build -> restart container
Tolong buatkan:
1) langkah-langkah deploy
2) script deploy.sh
3) catatan penting (env, DB volume, network, port)
Berikut detail project:
- Repo GitHub: <url>
- Path repo di VPS: <path>
- Nama image/container: <name>
- Port app: <port>
- Network docker: <network>
- Env vars penting: <key=value>
- Volume mount: <host_path>:<container_path>
```
