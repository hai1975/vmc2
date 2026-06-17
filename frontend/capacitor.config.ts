import type { CapacitorConfig } from '@capacitor/cli'

const config: CapacitorConfig = {
  appId: 'us.vmclinic.formassistant',
  appName: 'VM Clinic Forms',
  webDir: 'dist',
  server: {
    androidScheme: 'https',
  },
}

export default config
