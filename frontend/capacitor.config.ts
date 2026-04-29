import type { CapacitorConfig } from '@capacitor/cli';

const config: CapacitorConfig = {
  appId: 'com.trading.smcict',
  appName: 'SMC ICT Analyzer',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
    // When developing: point to your local backend
    // url: 'http://10.0.2.2:8000',
    // cleartext: true,
  },
  android: {
    buildOptions: {
      keystorePath: undefined,
      keystoreAlias: undefined,
    },
  },
  plugins: {
    SplashScreen: {
      launchShowDuration: 2000,
      backgroundColor: '#0d1117',
      showSpinner: false,
      androidSpinnerStyle: 'small',
      spinnerColor: '#26a69a',
    },
  },
};

export default config;
