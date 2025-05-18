# UI Component Library

## Design System

### 1. Colors
```scss
// Primary colors
$primary-50: #f0f9ff;
$primary-100: #e0f2fe;
$primary-500: #0ea5e9;
$primary-700: #0369a1;

// Status colors
$success: #22c55e;
$warning: #f59e0b;
$error: #ef4444;
$info: #3b82f6;

// Neutral colors
$gray-50: #f9fafb;
$gray-100: #f3f4f6;
$gray-700: #374151;
$gray-900: #111827;
```

### 2. Typography
```scss
// Font families
$font-sans: 'Inter', system-ui, sans-serif;
$font-mono: 'JetBrains Mono', monospace;

// Font sizes
$text-xs: 0.75rem;
$text-sm: 0.875rem;
$text-base: 1rem;
$text-lg: 1.125rem;
$text-xl: 1.25rem;
```

### 3. Spacing
```scss
// Base spacing units
$spacing-1: 0.25rem;
$spacing-2: 0.5rem;
$spacing-4: 1rem;
$spacing-6: 1.5rem;
$spacing-8: 2rem;
```

## Base Components

### 1. Button
```vue
<!-- components/base/Button.vue -->
<template>
  <button
    :class="[
      'inline-flex items-center px-4 py-2 rounded-md',
      'focus:outline-none focus:ring-2',
      variantClasses[variant],
      sizeClasses[size],
      { 'opacity-50 cursor-not-allowed': disabled }
    ]"
    :disabled="disabled || loading"
  >
    <Spinner v-if="loading" class="mr-2" />
    <slot />
  </button>
</template>

<script setup lang="ts">
interface Props {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  disabled?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
  loading: false,
  disabled: false
});
</script>
```

### 2. Status Badge
```vue
<!-- components/base/StatusBadge.vue -->
<template>
  <span
    :class="[
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
      statusClasses[status]
    ]"
  >
    <StatusIcon :status="status" class="mr-1" />
    {{ label }}
  </span>
</template>

<script setup lang="ts">
interface Props {
  status: 'success' | 'warning' | 'error' | 'info';
  label: string;
}

defineProps<Props>();
</script>
```

### 3. Card
```vue
<!-- components/base/Card.vue -->
<template>
  <div
    :class="[
      'bg-white rounded-lg shadow',
      'dark:bg-gray-800',
      padded && 'p-6'
    ]"
  >
    <div v-if="$slots.header" class="border-b pb-4 mb-4">
      <slot name="header" />
    </div>
    <slot />
    <div v-if="$slots.footer" class="border-t pt-4 mt-4">
      <slot name="footer" />
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  padded?: boolean;
}

withDefaults(defineProps<Props>(), {
  padded: true
});
</script>
```

## Form Components

### 1. Input Field
```vue
<!-- components/form/Input.vue -->
<template>
  <div>
    <label
      v-if="label"
      :for="id"
      class="block text-sm font-medium text-gray-700 dark:text-gray-300"
    >
      {{ label }}
    </label>
    <div class="mt-1 relative">
      <input
        :id="id"
        v-model="inputValue"
        :type="type"
        :class="[
          'block w-full rounded-md',
          'border-gray-300 dark:border-gray-600',
          'focus:ring-primary-500 focus:border-primary-500',
          { 'border-error-300': error }
        ]"
        v-bind="$attrs"
        @input="emit('update:modelValue', $event.target.value)"
      />
      <div
        v-if="error"
        class="absolute inset-y-0 right-0 pr-3 flex items-center"
      >
        <ExclamationCircleIcon class="h-5 w-5 text-error-400" />
      </div>
    </div>
    <p v-if="error" class="mt-2 text-sm text-error-600">
      {{ error }}
    </p>
  </div>
</template>

<script setup lang="ts">
interface Props {
  modelValue: string;
  label?: string;
  type?: string;
  error?: string;
  id?: string;
}

const props = withDefaults(defineProps<Props>(), {
  type: 'text'
});

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void;
}>();
</script>
```

### 2. Select Field
```vue
<!-- components/form/Select.vue -->
<template>
  <div>
    <label
      v-if="label"
      :for="id"
      class="block text-sm font-medium text-gray-700 dark:text-gray-300"
    >
      {{ label }}
    </label>
    <select
      :id="id"
      v-model="selectedValue"
      :class="[
        'mt-1 block w-full rounded-md',
        'border-gray-300 dark:border-gray-600',
        'focus:ring-primary-500 focus:border-primary-500'
      ]"
      @change="emit('update:modelValue', $event.target.value)"
    >
      <option
        v-for="option in options"
        :key="option.value"
        :value="option.value"
      >
        {{ option.label }}
      </option>
    </select>
  </div>
</template>

<script setup lang="ts">
interface Option {
  label: string;
  value: string | number;
}

interface Props {
  modelValue: string | number;
  options: Option[];
  label?: string;
  id?: string;
}

defineProps<Props>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: string | number): void;
}>();
</script>
```

## Data Display Components

### 1. Metrics Card
```vue
<!-- components/data/MetricsCard.vue -->
<template>
  <Card>
    <template #header>
      <div class="flex justify-between items-center">
        <h3 class="text-lg font-medium">{{ title }}</h3>
        <StatusBadge
          v-if="status"
          :status="status"
          :label="statusLabel"
        />
      </div>
    </template>

    <div class="space-y-4">
      <div class="flex items-baseline">
        <div class="text-2xl font-semibold">{{ value }}</div>
        <div
          v-if="change"
          :class="[
            'ml-2 text-sm',
            change > 0 ? 'text-success-600' : 'text-error-600'
          ]"
        >
          {{ change > 0 ? '+' : '' }}{{ change }}%
        </div>
      </div>

      <LineChart
        v-if="data"
        :data="data"
        :options="chartOptions"
      />
    </div>
  </Card>
</template>

<script setup lang="ts">
interface Props {
  title: string;
  value: string | number;
  change?: number;
  status?: 'success' | 'warning' | 'error';
  statusLabel?: string;
  data?: ChartData;
}

defineProps<Props>();
</script>
```

### 2. Data Table
```vue
<!-- components/data/Table.vue -->
<template>
  <div class="overflow-x-auto">
    <table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50 dark:bg-gray-700">
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            :class="[
              'px-6 py-3 text-left text-xs font-medium',
              'text-gray-500 dark:text-gray-300 uppercase tracking-wider'
            ]"
          >
            {{ column.label }}
          </th>
        </tr>
      </thead>
      <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200">
        <tr v-for="row in data" :key="row.id">
          <td
            v-for="column in columns"
            :key="column.key"
            class="px-6 py-4 whitespace-nowrap"
          >
            <slot
              :name="column.key"
              :value="row[column.key]"
              :row="row"
            >
              {{ row[column.key] }}
            </slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
interface Column {
  key: string;
  label: string;
}

interface Props {
  columns: Column[];
  data: Record<string, any>[];
}

defineProps<Props>();
</script>
```

## Layout Components

### 1. Page Layout
```vue
<!-- components/layout/Page.vue -->
<template>
  <div class="min-h-screen bg-gray-100 dark:bg-gray-900">
    <Sidebar />
    <div class="pl-64">
      <Header />
      <main class="py-6">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div v-if="title" class="pb-5 border-b border-gray-200">
            <h1 class="text-2xl font-bold">{{ title }}</h1>
          </div>
          <div class="mt-6">
            <slot />
          </div>
        </div>
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title?: string;
}

defineProps<Props>();
</script>
```

### 2. Grid Layout
```vue
<!-- components/layout/Grid.vue -->
<template>
  <div
    :class="[
      'grid gap-6',
      columns && `grid-cols-${columns}`,
      responsive && 'md:grid-cols-2 lg:grid-cols-3'
    ]"
  >
    <slot />
  </div>
</template>

<script setup lang="ts">
interface Props {
  columns?: number;
  responsive?: boolean;
}

withDefaults(defineProps<Props>(), {
  responsive: true
});
</script>
```

## Usage Examples

### 1. Service Status Page
```vue
<template>
  <Page title="Service Status">
    <Grid>
      <MetricsCard
        v-for="service in services"
        :key="service.id"
        :title="service.name"
        :value="service.status"
        :status="service.health"
        :data="service.metrics"
      />
    </Grid>

    <Card class="mt-6">
      <Table
        :columns="columns"
        :data="services"
      >
        <template #status="{ value }">
          <StatusBadge
            :status="value.toLowerCase()"
            :label="value"
          />
        </template>
      </Table>
    </Card>
  </Page>
</template>
```

### 2. Configuration Form
```vue
<template>
  <Page title="Service Configuration">
    <Card>
      <form @submit.prevent="saveConfig">
        <div class="space-y-6">
          <Input
            v-model="config.name"
            label="Service Name"
            :error="errors.name"
          />

          <Select
            v-model="config.type"
            :options="serviceTypes"
            label="Service Type"
          />

          <Button
            type="submit"
            :loading="saving"
          >
            Save Configuration
          </Button>
        </div>
      </form>
    </Card>
  </Page>
</template>
``` 