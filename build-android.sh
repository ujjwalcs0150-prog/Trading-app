#!/bin/bash
# ─────────────────────────────────────────────────────────────────
#  Build Android APK for SMC/ICT Trading Analyzer
#  Prerequisites: Android Studio + SDK installed, JAVA_HOME set
# ─────────────────────────────────────────────────────────────────
set -e

BACKEND_IP="${BACKEND_IP:-10.0.2.2}"   # override: BACKEND_IP=192.168.1.x ./build-android.sh
BUILD_TYPE="${BUILD_TYPE:-debug}"        # debug | release

echo "=== SMC/ICT Analyzer — Android Build ==="
echo "  Backend IP : $BACKEND_IP:8000"
echo "  Build type : $BUILD_TYPE"
echo ""

cd "$(dirname "$0")/frontend"

# 1. Build web assets with the Android API URL injected
echo "[1/4] Building web assets..."
VITE_API_URL="http://${BACKEND_IP}:8000" npx vite build --mode android

# 2. Sync to Android platform
echo "[2/4] Syncing to Android..."
npx cap sync android

# 3. Gradle build
echo "[3/4] Running Gradle build ($BUILD_TYPE)..."
cd android
if [ "$BUILD_TYPE" = "release" ]; then
    ./gradlew assembleRelease
    APK_PATH="app/build/outputs/apk/release/app-release-unsigned.apk"
else
    ./gradlew assembleDebug
    APK_PATH="app/build/outputs/apk/debug/app-debug.apk"
fi

echo ""
echo "[4/4] Done!"
echo "  APK → frontend/android/${APK_PATH}"
echo ""
echo "Install on connected device:"
echo "  adb install android/${APK_PATH}"
