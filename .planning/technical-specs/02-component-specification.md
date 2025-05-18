# Component Specification

## Core Components

### 1. Dashboard (`Dashboard.vue`)
```typescript
interface DashboardProps {
  initialStatus: InitializationStatus;
  services: ServiceStatus[];
  metrics: SystemMetrics;
}

interface DashboardEmits {
  (e: 'initialize', options: InitializationOptions): void;
  (e: 'refresh'): void;
}

// Component Implementation
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useInitializationStore } from '@/stores/initialization';
import { useMetricsStore } from '@/stores/metrics';
import { useWebSocket } from '@/composables/websocket';

const props = defineProps<DashboardProps>();
const emit = defineEmits<DashboardEmits>();

const initializationStore = useInitializationStore();
const metricsStore = useMetricsStore();
const { connect, subscribe } = useWebSocket();

// Real-time updates
onMounted(() => {
  connect();
  subscribe('initialization.status', (data) => {
    initializationStore.updateStatus(data);
  });
  subscribe('metrics.update', (data) => {
    metricsStore.updateMetrics(data);
  });
});
</script>
```

### 2. Service Manager (`ServiceManager.vue`)
```typescript
interface ServiceManagerProps {
  services: ServiceStatus[];
  loading: boolean;
}

interface ServiceManagerEmits {
  (e: 'control', serviceId: string, action: ServiceAction): void;
  (e: 'refresh'): void;
}

// Component Implementation
<script setup lang="ts">
import { ref } from 'vue';
import { useServiceStore } from '@/stores/services';
import { useWebSocket } from '@/composables/websocket';

const props = defineProps<ServiceManagerProps>();
const emit = defineEmits<ServiceManagerEmits>();

const serviceStore = useServiceStore();
const { subscribe } = useWebSocket();

// Service control methods
const handleServiceAction = async (serviceId: string, action: ServiceAction) => {
  try {
    await serviceStore.controlService(serviceId, action);
    emit('refresh');
  } catch (error) {
    // Handle error
  }
};
</script>
```

### 3. Configuration Manager (`ConfigurationManager.vue`)
```typescript
interface ConfigurationManagerProps {
  config: SystemConfig;
  loading: boolean;
}

interface ConfigurationManagerEmits {
  (e: 'update', config: Partial<SystemConfig>): void;
  (e: 'reset'): void;
}

// Component Implementation
<script setup lang="ts">
import { ref } from 'vue';
import { useForm } from 'vee-validate';
import { useConfigStore } from '@/stores/config';

const props = defineProps<ConfigurationManagerProps>();
const emit = defineEmits<ConfigurationManagerEmits>();

const configStore = useConfigStore();
const { handleSubmit, errors } = useForm({
  validationSchema: configSchema
});

const onSubmit = handleSubmit(async (values) => {
  try {
    await configStore.updateConfig(values);
    emit('update', values);
  } catch (error) {
    // Handle error
  }
});
</script>
```

## Store Definitions

### 1. Initialization Store
```typescript
// stores/initialization.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useApi } from '@/composables/api';

export const useInitializationStore = defineStore('initialization', () => {
  const status = ref<InitializationStatus | null>(null);
  const loading = ref(false);
  const error = ref<Error | null>(null);

  const api = useApi();

  const startInitialization = async (options: InitializationOptions) => {
    loading.value = true;
    try {
      const response = await api.post('/initialize', options);
      status.value = response.data;
    } catch (err) {
      error.value = err;
    } finally {
      loading.value = false;
    }
  };

  const updateStatus = (newStatus: InitializationStatus) => {
    status.value = newStatus;
  };

  return {
    status,
    loading,
    error,
    startInitialization,
    updateStatus
  };
});
```

### 2. Service Store
```typescript
// stores/services.ts
import { defineStore } from 'pinia';
import { ref } from 'vue';
import { useApi } from '@/composables/api';

export const useServiceStore = defineStore('services', () => {
  const services = ref<ServiceStatus[]>([]);
  const loading = ref(false);
  const error = ref<Error | null>(null);

  const api = useApi();

  const fetchServices = async () => {
    loading.value = true;
    try {
      const response = await api.get('/services');
      services.value = response.data.services;
    } catch (err) {
      error.value = err;
    } finally {
      loading.value = false;
    }
  };

  const controlService = async (serviceId: string, action: ServiceAction) => {
    loading.value = true;
    try {
      await api.post(`/services/${serviceId}/control`, { action });
      await fetchServices();
    } catch (err) {
      error.value = err;
    } finally {
      loading.value = false;
    }
  };

  return {
    services,
    loading,
    error,
    fetchServices,
    controlService
  };
});
```

## Composable Functions

### 1. WebSocket Composable
```typescript
// composables/websocket.ts
import { ref } from 'vue';

export function useWebSocket() {
  const socket = ref<WebSocket | null>(null);
  const connected = ref(false);
  const error = ref<Error | null>(null);

  const connect = () => {
    socket.value = new WebSocket(import.meta.env.VITE_WS_URL);
    
    socket.value.onopen = () => {
      connected.value = true;
    };

    socket.value.onerror = (err) => {
      error.value = err;
      connected.value = false;
    };

    socket.value.onclose = () => {
      connected.value = false;
    };
  };

  const subscribe = (event: string, callback: (data: any) => void) => {
    if (!socket.value) return;

    socket.value.onmessage = (message) => {
      const data = JSON.parse(message.data);
      if (data.event === event) {
        callback(data.data);
      }
    };
  };

  return {
    socket,
    connected,
    error,
    connect,
    subscribe
  };
}
```

### 2. API Composable
```typescript
// composables/api.ts
import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

export function useApi() {
  const authStore = useAuthStore();
  
  const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    headers: {
      'Content-Type': 'application/json'
    }
  });

  api.interceptors.request.use((config) => {
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`;
    }
    return config;
  });

  return api;
}
```

## Type Definitions

### 1. System Types
```typescript
// types/system.ts
export type InitializationStatus = {
  id: string;
  status: 'PENDING' | 'INITIALIZING' | 'COMPLETED' | 'ERROR';
  started_at: string;
  completed_at?: string;
  components: Record<string, string>;
  metrics?: {
    total_time: number;
    [key: string]: number;
  };
};

export type ServiceStatus = {
  id: string;
  name: string;
  status: 'RUNNING' | 'STOPPED' | 'ERROR';
  health: 'HEALTHY' | 'UNHEALTHY';
  last_check: string;
};

export type SystemConfig = {
  database: {
    host: string;
    port: number;
    name: string;
  };
  cache: {
    driver: string;
    host: string;
    port: number;
  };
  queue: {
    driver: string;
    host: string;
    port: number;
  };
};

export type SystemMetrics = {
  cpu: {
    usage: number;
    cores: number;
  };
  memory: {
    used: number;
    total: number;
  };
  services: Record<string, {
    [key: string]: number;
  }>;
};
```

## Component Styling

### 1. Tailwind Configuration
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          // ... more colors
        }
      },
      spacing: {
        '72': '18rem',
        '84': '21rem',
        '96': '24rem',
      }
    }
  },
  plugins: [
    require('@tailwindcss/forms'),
    require('@tailwindcss/typography'),
    require('@tailwindcss/aspect-ratio'),
  ]
}
```

### 2. Component Styles
```scss
// styles/components.scss
.dashboard {
  @apply grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4;
  
  &-card {
    @apply bg-white rounded-lg shadow p-4;
    
    &-header {
      @apply flex items-center justify-between mb-4;
    }
    
    &-content {
      @apply space-y-2;
    }
  }
}

.service-manager {
  @apply space-y-4;
  
  &-list {
    @apply divide-y divide-gray-200;
  }
  
  &-item {
    @apply py-4 flex items-center justify-between;
    
    &-status {
      @apply inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium;
      
      &.running {
        @apply bg-green-100 text-green-800;
      }
      
      &.stopped {
        @apply bg-red-100 text-red-800;
      }
    }
  }
}
``` 