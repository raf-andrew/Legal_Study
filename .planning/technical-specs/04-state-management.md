# State Management Specification

## Store Structure

### 1. Authentication Store
```typescript
// stores/auth.ts
interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  permissions: string[];
}

interface AuthActions {
  login(credentials: Credentials): Promise<void>;
  logout(): Promise<void>;
  refreshToken(): Promise<void>;
  updatePermissions(): Promise<void>;
}

interface AuthGetters {
  hasPermission: (permission: string) => boolean;
  isAdmin: boolean;
  userInitials: string;
}
```

### 2. Initialization Store
```typescript
// stores/initialization.ts
interface InitializationState {
  status: InitializationStatus;
  components: Record<string, ComponentStatus>;
  progress: number;
  error: Error | null;
  history: InitializationHistory[];
}

interface InitializationActions {
  startInitialization(options: InitOptions): Promise<void>;
  cancelInitialization(): Promise<void>;
  retryComponent(componentId: string): Promise<void>;
  updateStatus(status: InitializationStatus): void;
}

interface InitializationGetters {
  isInitializing: boolean;
  failedComponents: string[];
  lastInitialization: InitializationHistory;
}
```

### 3. Service Store
```typescript
// stores/services.ts
interface ServiceState {
  services: Record<string, ServiceStatus>;
  activeService: string | null;
  healthChecks: Record<string, HealthCheck[]>;
  metrics: Record<string, ServiceMetrics>;
}

interface ServiceActions {
  fetchServices(): Promise<void>;
  controlService(serviceId: string, action: ServiceAction): Promise<void>;
  updateServiceStatus(serviceId: string, status: ServiceStatus): void;
  updateHealthChecks(serviceId: string): Promise<void>;
}

interface ServiceGetters {
  runningServices: ServiceStatus[];
  failedServices: ServiceStatus[];
  serviceHealth: (serviceId: string) => HealthStatus;
}
```

### 4. Configuration Store
```typescript
// stores/config.ts
interface ConfigState {
  configs: Record<string, any>;
  templates: ConfigTemplate[];
  validation: Record<string, ValidationResult>;
  history: ConfigHistory[];
}

interface ConfigActions {
  loadConfig(serviceId: string): Promise<void>;
  saveConfig(serviceId: string, config: any): Promise<void>;
  validateConfig(serviceId: string, config: any): Promise<ValidationResult>;
  revertConfig(serviceId: string, version: string): Promise<void>;
}

interface ConfigGetters {
  isValid: (serviceId: string) => boolean;
  hasChanges: (serviceId: string) => boolean;
  latestVersion: (serviceId: string) => string;
}
```

## Store Interactions

### 1. Initialization Flow
```typescript
// Example of store interactions during initialization
async function startSystemInitialization() {
  const auth = useAuthStore();
  const init = useInitializationStore();
  const services = useServiceStore();
  const config = useConfigStore();

  try {
    // Verify permissions
    if (!auth.hasPermission('initialize_system')) {
      throw new Error('Unauthorized');
    }

    // Load and validate configurations
    await config.loadConfig('system');
    const validation = await config.validateConfig('system', config.configs.system);
    if (!validation.isValid) {
      throw new Error('Invalid configuration');
    }

    // Start initialization
    await init.startInitialization({
      components: ['database', 'cache', 'queue'],
      validateOnly: false
    });

    // Monitor services
    await services.fetchServices();
  } catch (error) {
    // Handle errors
  }
}
```

### 2. Service Management Flow
```typescript
// Example of store interactions during service management
async function handleServiceFailure(serviceId: string) {
  const services = useServiceStore();
  const config = useConfigStore();
  const notifications = useNotificationStore();

  try {
    // Check service status
    const status = services.serviceHealth(serviceId);
    if (status === 'FAILED') {
      // Load service configuration
      await config.loadConfig(serviceId);
      
      // Attempt automatic recovery
      await services.controlService(serviceId, 'restart');
      
      // Monitor health checks
      await services.updateHealthChecks(serviceId);
      
      // Notify if still failing
      if (services.serviceHealth(serviceId) === 'FAILED') {
        notifications.add({
          type: 'error',
          message: `Service ${serviceId} recovery failed`
        });
      }
    }
  } catch (error) {
    // Handle errors
  }
}
```

## WebSocket Integration

### 1. Real-time Updates
```typescript
// composables/useWebSocket.ts
export function useWebSocket() {
  const init = useInitializationStore();
  const services = useServiceStore();
  const metrics = useMetricsStore();

  onMounted(() => {
    const socket = new WebSocket(import.meta.env.VITE_WS_URL);

    socket.onmessage = (event) => {
      const { type, data } = JSON.parse(event.data);

      switch (type) {
        case 'INITIALIZATION_UPDATE':
          init.updateStatus(data);
          break;
        case 'SERVICE_STATUS_UPDATE':
          services.updateServiceStatus(data.serviceId, data.status);
          break;
        case 'METRICS_UPDATE':
          metrics.updateMetrics(data);
          break;
      }
    };
  });
}
```

### 2. Event Handling
```typescript
// Example of WebSocket event handling in components
const handleServiceEvent = (event: ServiceEvent) => {
  const services = useServiceStore();
  const notifications = useNotificationStore();

  switch (event.type) {
    case 'STATUS_CHANGE':
      services.updateServiceStatus(event.serviceId, event.status);
      if (event.status === 'FAILED') {
        notifications.add({
          type: 'error',
          message: `Service ${event.serviceId} failed`
        });
      }
      break;
    case 'HEALTH_CHECK':
      services.updateHealthChecks(event.serviceId);
      break;
  }
};
```

## Persistence Layer

### 1. Local Storage
```typescript
// plugins/persistence.ts
export function setupStorePersistence() {
  const auth = useAuthStore();
  const config = useConfigStore();

  // Watch auth state
  watch(
    () => auth.token,
    (token) => {
      if (token) {
        localStorage.setItem('auth_token', token);
      } else {
        localStorage.removeItem('auth_token');
      }
    }
  );

  // Watch config changes
  watch(
    () => config.configs,
    (configs) => {
      localStorage.setItem('config_cache', JSON.stringify(configs));
    },
    { deep: true }
  );
}
```

### 2. API Integration
```typescript
// composables/useApi.ts
export function useApi() {
  const auth = useAuthStore();

  const api = axios.create({
    baseURL: import.meta.env.VITE_API_URL,
    headers: {
      'Content-Type': 'application/json'
    }
  });

  // Add auth token to requests
  api.interceptors.request.use((config) => {
    if (auth.token) {
      config.headers.Authorization = `Bearer ${auth.token}`;
    }
    return config;
  });

  // Handle token refresh
  api.interceptors.response.use(
    (response) => response,
    async (error) => {
      if (error.response.status === 401) {
        await auth.refreshToken();
        return api(error.config);
      }
      return Promise.reject(error);
    }
  );

  return api;
}
``` 