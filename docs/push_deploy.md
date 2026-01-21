# Push Deploy (Serial + Manual)

Alur ini memakai GitHub sebagai sumber utama, lalu update NAS secara manual.

## 1) Windows (VS Code / PowerShell)

```powershell
git add .
git commit -m "update ..."
git push origin main
```

## 2) NAS (manual deploy)

```bash
ssh root@10.144.197.242
cd /mnt/ssd/hosting/presensi-app
git pull origin main
docker build -t presensi-app:latest .
docker stop presensi-app && docker rm presensi-app
docker run -d --name presensi-app \
  --user 0:0 \
  --network hosting_web \
  -p 5050:5050 \
  -e FLASK_SECRET="ganti-dengan-secret-kuat" \
  -e PRESENSI_DB_PATH=/data/presensi.db \
  -v /mnt/ssd/hosting/presensi-app:/data \
  presensi-app:latest
```

## Opsional: gunakan skrip deploy di NAS

Jika sudah membuat `deploy.sh`, cukup jalankan:

```bash
cd /mnt/ssd/hosting/presensi-app
./deploy.sh
```

## Ringkas (harian)

1) Windows:

```powershell
git add .
git commit -m "update ..."
git push origin main
```

2) NAS:

```bash
cd /mnt/ssd/hosting/presensi-app
./deploy.sh
```

## Prompt template (project lain)

Gunakan template ini untuk minta setup deploy di project lain:

```
Saya mau setup workflow deploy manual serial:
- Coding di Windows (VS Code) → push ke GitHub
- Di NAS (Linux) → git pull → docker build → restart container
Tolong buatkan:
1) langkah-langkah deploy
2) script deploy.sh
3) catatan penting (env, DB volume, network, port)
Berikut detail project:
- Repo GitHub: <url>
- Path repo di NAS: <path>
- Nama image/container: <name>
- Port app: <port>
- Network docker: <network>
- Env vars penting: <key=value>
- Volume mount: <host_path>:<container_path>
```
