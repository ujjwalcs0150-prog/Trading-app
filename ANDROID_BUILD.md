# Building the Android APK

## Prerequisites

| Tool | Version |
|------|---------|
| Android Studio | Hedgehog 2023.1+ |
| JDK | 17 or 21 |
| Android SDK | API 34 (compile), API 22 (min) |
| Node.js | 18+ |

---

## Quick build (recommended)

```bash
# 1. Start the Python backend first
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000

# 2. Build APK (from repo root)
#    Replace 192.168.1.x with your machine's LAN IP for physical devices
BACKEND_IP=10.0.2.2 ./build-android.sh        # emulator
BACKEND_IP=192.168.1.100 ./build-android.sh   # physical device
```

The debug APK will be at:
```
frontend/android/app/build/outputs/apk/debug/app-debug.apk
```

Install on a connected device / emulator:
```bash
adb install frontend/android/app/build/outputs/apk/debug/app-debug.apk
```

---

## Manual steps (Android Studio)

```bash
# 1. Build web assets with your backend IP
cd frontend
VITE_API_URL=http://10.0.2.2:8000 npm run build:android

# 2. Sync web assets into the Android project
npx cap sync android

# 3. Open in Android Studio
npx cap open android
# → Run ▶ or Build → Build APK(s)
```

---

## Backend connectivity

| Scenario | `VITE_API_URL` |
|----------|----------------|
| Android Emulator | `http://10.0.2.2:8000` |
| Physical device (same WiFi) | `http://<your-LAN-IP>:8000` |
| Remote server | `https://<your-domain>` |

The backend URL is baked into the APK at build time via `VITE_API_URL`.
To change it, rebuild with the new URL and reinstall.

---

## Release build

```bash
BUILD_TYPE=release BACKEND_IP=your.server.com ./build-android.sh
# Then sign the APK with your keystore before uploading to Play Store
```
