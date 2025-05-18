# API Specification

## 1. Authentication API

### Token Management
```typescript
interface AuthToken {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  token_type: string;
}

// POST /api/auth/login
interface LoginRequest {
  email: string;
  password: string;
  remember_me?: boolean;
}

// POST /api/auth/refresh
interface RefreshRequest {
  refresh_token: string;
}

// POST /api/auth/logout
interface LogoutRequest {
  token: string;
}
```

### Session Management
```typescript
interface Session {
  id: string;
  user_id: string;
  ip_address: string;
  user_agent: string;
  last_activity: string;
  created_at: string;
}

// GET /api/auth/sessions
interface SessionListResponse {
  sessions: Session[];
  current_session_id: string;
}

// DELETE /api/auth/sessions/{id}
interface SessionDeleteResponse {
  success: boolean;
}
```

## 2. Configuration API

### System Settings
```typescript
interface SystemConfig {
  general: {
    site_name: string;
    timezone: string;
    locale: string;
  };
  security: {
    password_policy: {
      min_length: number;
      require_special: boolean;
    };
    session_timeout: number;
  };
  modules: {
    enabled: string[];
    disabled: string[];
  };
}

// GET /api/config
interface ConfigResponse {
  config: SystemConfig;
  last_updated: string;
}

// PUT /api/config
interface ConfigUpdateRequest {
  config: Partial<SystemConfig>;
}
```

### Profile Management
```typescript
interface ConfigProfile {
  id: string;
  name: string;
  description: string;
  config: SystemConfig;
  created_at: string;
  updated_at: string;
}

// GET /api/config/profiles
interface ProfileListResponse {
  profiles: ConfigProfile[];
}

// POST /api/config/profiles
interface ProfileCreateRequest {
  name: string;
  description: string;
  config: SystemConfig;
}

// PUT /api/config/profiles/{id}
interface ProfileUpdateRequest {
  name?: string;
  description?: string;
  config?: SystemConfig;
}
```

## 3. Module API

### Module Management
```typescript
interface Module {
  id: string;
  name: string;
  description: string;
  version: string;
  author: string;
  dependencies: string[];
  status: 'installed' | 'available' | 'updating';
  settings: Record<string, any>;
}

// GET /api/modules
interface ModuleListResponse {
  modules: Module[];
}

// POST /api/modules/install
interface ModuleInstallRequest {
  module_id: string;
  version?: string;
}

// PUT /api/modules/{id}
interface ModuleUpdateRequest {
  settings?: Record<string, any>;
  enabled?: boolean;
}
```

### Module Marketplace
```typescript
interface MarketplaceModule {
  id: string;
  name: string;
  description: string;
  latest_version: string;
  author: string;
  downloads: number;
  rating: number;
  dependencies: string[];
  tags: string[];
}

// GET /api/modules/marketplace
interface MarketplaceResponse {
  modules: MarketplaceModule[];
  categories: string[];
  tags: string[];
}
```

## 4. System Status API

### Status Monitoring
```typescript
interface SystemStatus {
  initialization: {
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
    progress: number;
    current_step: string;
  };
  modules: {
    total: number;
    active: number;
    errors: number;
  };
  performance: {
    memory_usage: number;
    cpu_usage: number;
    response_time: number;
  };
}

// GET /api/status
interface StatusResponse {
  status: SystemStatus;
  last_updated: string;
}
```

### Activity Logging
```typescript
interface ActivityLog {
  id: string;
  type: string;
  user_id: string;
  description: string;
  metadata: Record<string, any>;
  created_at: string;
}

// GET /api/activity
interface ActivityListResponse {
  activities: ActivityLog[];
  total: number;
  page: number;
  per_page: number;
}
```

## 5. WebSocket Events

### System Events
```typescript
interface SystemEvent {
  type: 'status_update' | 'error' | 'notification';
  data: {
    status?: SystemStatus;
    error?: {
      code: string;
      message: string;
      details?: any;
    };
    notification?: {
      type: 'info' | 'success' | 'warning' | 'error';
      message: string;
      action?: {
        type: string;
        payload: any;
      };
    };
  };
}
```

### User Events
```typescript
interface UserEvent {
  type: 'activity' | 'session' | 'preference';
  data: {
    activity?: ActivityLog;
    session?: {
      id: string;
      action: 'start' | 'end' | 'timeout';
    };
    preference?: {
      key: string;
      value: any;
    };
  };
}
```

## 6. Error Responses

### Error Format
```typescript
interface ErrorResponse {
  error: {
    code: string;
    message: string;
    details?: any;
  };
  status: number;
}
```

### Common Error Codes
- `AUTH_REQUIRED`: Authentication required
- `INVALID_TOKEN`: Invalid or expired token
- `PERMISSION_DENIED`: Insufficient permissions
- `VALIDATION_ERROR`: Request validation failed
- `MODULE_ERROR`: Module operation failed
- `SYSTEM_ERROR`: Internal system error 