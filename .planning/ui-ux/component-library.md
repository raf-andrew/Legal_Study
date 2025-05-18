# Component Library

## Core Components

### 1. Initialization Wizard

#### Props
```typescript
interface WizardProps {
  steps: WizardStep[];
  onComplete: () => void;
  onError: (error: Error) => void;
}

interface WizardStep {
  id: string;
  title: string;
  component: Component;
  validation?: () => Promise<boolean>;
}
```

#### Usage
```vue
<template>
  <InitializationWizard
    :steps="wizardSteps"
    @complete="handleComplete"
    @error="handleError"
  />
</template>

<script setup lang="ts">
const wizardSteps = [
  {
    id: 'welcome',
    title: 'Welcome',
    component: WelcomeStep,
  },
  {
    id: 'configuration',
    title: 'Configuration',
    component: ConfigurationStep,
    validation: validateConfiguration,
  },
  // ... more steps
];
</script>
```

### 2. Status Card

#### Props
```typescript
interface StatusCardProps {
  title: string;
  status: 'success' | 'warning' | 'error' | 'info';
  value: string | number;
  icon?: Component;
  trend?: {
    direction: 'up' | 'down';
    value: number;
  };
}
```

#### Usage
```vue
<template>
  <StatusCard
    title="Database Status"
    status="success"
    value="Connected"
    :icon="DatabaseIcon"
    :trend="{ direction: 'up', value: 5 }"
  />
</template>
```

### 3. Configuration Editor

#### Props
```typescript
interface ConfigEditorProps {
  schema: JSONSchema;
  value: Record<string, any>;
  onChange: (value: Record<string, any>) => void;
  onValidate: (errors: ValidationError[]) => void;
}
```

#### Usage
```vue
<template>
  <ConfigEditor
    :schema="configSchema"
    :value="currentConfig"
    @change="handleConfigChange"
    @validate="handleValidation"
  />
</template>
```

### 4. Service Monitor

#### Props
```typescript
interface ServiceMonitorProps {
  services: Service[];
  metrics: Record<string, ServiceMetrics>;
  onAction: (action: ServiceAction) => void;
  refreshInterval?: number;
}
```

#### Usage
```vue
<template>
  <ServiceMonitor
    :services="activeServices"
    :metrics="serviceMetrics"
    @action="handleServiceAction"
    :refresh-interval="5000"
  />
</template>
```

## Layout Components

### 1. Dashboard Layout

#### Props
```typescript
interface DashboardLayoutProps {
  sidebar?: Component;
  header?: Component;
  footer?: Component;
  loading?: boolean;
}
```

#### Usage
```vue
<template>
  <DashboardLayout
    :sidebar="NavigationSidebar"
    :header="AppHeader"
    :footer="AppFooter"
    :loading="isLoading"
  >
    <router-view />
  </DashboardLayout>
</template>
```

### 2. Grid Layout

#### Props
```typescript
interface GridLayoutProps {
  columns: number;
  gap?: string;
  responsive?: boolean;
}
```

#### Usage
```vue
<template>
  <GridLayout :columns="3" gap="1rem" :responsive="true">
    <StatusCard v-for="service in services" :key="service.id" :service="service" />
  </GridLayout>
</template>
```

## Form Components

### 1. Form Input

#### Props
```typescript
interface FormInputProps {
  label: string;
  type?: string;
  modelValue: string | number;
  error?: string;
  required?: boolean;
  disabled?: boolean;
}
```

#### Usage
```vue
<template>
  <FormInput
    label="Database Host"
    type="text"
    v-model="dbHost"
    :error="errors.dbHost"
    required
  />
</template>
```

### 2. Form Select

#### Props
```typescript
interface FormSelectProps {
  label: string;
  options: SelectOption[];
  modelValue: string | number;
  error?: string;
  required?: boolean;
  disabled?: boolean;
}

interface SelectOption {
  value: string | number;
  label: string;
}
```

#### Usage
```vue
<template>
  <FormSelect
    label="Database Type"
    :options="dbTypes"
    v-model="selectedDbType"
    :error="errors.dbType"
    required
  />
</template>
```

## Feedback Components

### 1. Alert System

#### Props
```typescript
interface AlertSystemProps {
  alerts: Alert[];
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  autoDismiss?: boolean;
  dismissTimeout?: number;
}

interface Alert {
  id: string;
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
  timestamp: string;
}
```

#### Usage
```vue
<template>
  <AlertSystem
    :alerts="activeAlerts"
    position="top-right"
    :auto-dismiss="true"
    :dismiss-timeout="5000"
  />
</template>
```

### 2. Progress Indicator

#### Props
```typescript
interface ProgressIndicatorProps {
  progress: number;
  status: 'running' | 'completed' | 'failed';
  message?: string;
  showPercentage?: boolean;
}
```

#### Usage
```vue
<template>
  <ProgressIndicator
    :progress="initializationProgress"
    :status="initializationStatus"
    message="Initializing database..."
    :show-percentage="true"
  />
</template>
```

## Data Visualization

### 1. Metrics Chart

#### Props
```typescript
interface MetricsChartProps {
  type: 'line' | 'bar' | 'pie';
  data: ChartData;
  options?: ChartOptions;
  height?: string;
}

interface ChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor?: string;
  }[];
}
```

#### Usage
```vue
<template>
  <MetricsChart
    type="line"
    :data="performanceData"
    :options="chartOptions"
    height="300px"
  />
</template>
```

### 2. Status Timeline

#### Props
```typescript
interface StatusTimelineProps {
  events: TimelineEvent[];
  maxEvents?: number;
}

interface TimelineEvent {
  timestamp: string;
  type: 'success' | 'warning' | 'error' | 'info';
  message: string;
  details?: string;
}
```

#### Usage
```vue
<template>
  <StatusTimeline
    :events="serviceEvents"
    :max-events="10"
  />
</template>
```

## Utility Components

### 1. Loading State

#### Props
```typescript
interface LoadingStateProps {
  message?: string;
  size?: 'sm' | 'md' | 'lg';
  fullscreen?: boolean;
}
```

#### Usage
```vue
<template>
  <LoadingState
    message="Loading configuration..."
    size="md"
    :fullscreen="false"
  />
</template>
```

### 2. Empty State

#### Props
```typescript
interface EmptyStateProps {
  title: string;
  message: string;
  icon?: Component;
  action?: {
    label: string;
    handler: () => void;
  };
}
```

#### Usage
```vue
<template>
  <EmptyState
    title="No Services Found"
    message="Add a new service to get started"
    :icon="PlusIcon"
    :action="{
      label: 'Add Service',
      handler: addNewService
    }"
  />
</template>
``` 