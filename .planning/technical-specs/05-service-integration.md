# Service Integration Specification

## Integration Methods

### 1. Laravel Package Integration
```php
// config/modular-initialization.php
return [
    'services' => [
        'database' => [
            'class' => \LegalStudy\ModularInitialization\Services\DatabaseInitialization::class,
            'config' => [
                'connection' => env('DB_CONNECTION', 'mysql'),
                'timeout' => env('DB_TIMEOUT', 30)
            ]
        ],
        'cache' => [
            'class' => \LegalStudy\ModularInitialization\Services\CacheInitialization::class,
            'config' => [
                'driver' => env('CACHE_DRIVER', 'redis'),
                'prefix' => env('CACHE_PREFIX', 'legal_study')
            ]
        ]
    ],
    'websocket' => [
        'enabled' => env('INIT_WEBSOCKET_ENABLED', true),
        'host' => env('INIT_WEBSOCKET_HOST', '127.0.0.1'),
        'port' => env('INIT_WEBSOCKET_PORT', 6001)
    ],
    'monitoring' => [
        'enabled' => env('INIT_MONITORING_ENABLED', true),
        'metrics_interval' => env('INIT_METRICS_INTERVAL', 60)
    ]
];
```

### 2. Service Provider Registration
```php
// app/Providers/ModularInitializationServiceProvider.php
namespace App\Providers;

use Illuminate\Support\ServiceProvider;
use LegalStudy\ModularInitialization\Facades\Initialization;

class ModularInitializationServiceProvider extends ServiceProvider
{
    public function register()
    {
        $this->app->singleton('initialization', function ($app) {
            return new \LegalStudy\ModularInitialization\InitializationManager(
                $app,
                config('modular-initialization')
            );
        });
    }

    public function boot()
    {
        if ($this->app->runningInConsole()) {
            $this->publishes([
                __DIR__.'/../config/modular-initialization.php' => config_path('modular-initialization.php'),
            ], 'config');

            $this->publishes([
                __DIR__.'/../database/migrations' => database_path('migrations'),
            ], 'migrations');
        }
    }
}
```

### 3. Frontend Integration
```typescript
// resources/js/app.ts
import { createApp } from 'vue';
import { createInertiaApp } from '@inertiajs/vue3';
import { initializeServices } from '@legal-study/modular-initialization-ui';

createInertiaApp({
    resolve: name => {
        const pages = import.meta.glob('./Pages/**/*.vue', { eager: true });
        return pages[`./Pages/${name}.vue`];
    },
    setup({ el, App, props, plugin }) {
        const app = createApp({ render: () => h(App, props) });
        
        // Initialize services
        initializeServices({
            websocket: {
                host: import.meta.env.VITE_WS_HOST,
                port: import.meta.env.VITE_WS_PORT
            },
            api: {
                baseUrl: import.meta.env.VITE_API_URL
            }
        });

        app.use(plugin);
        app.mount(el);
    },
});
```

## API Integration

### 1. REST API
```php
// routes/api.php
use LegalStudy\ModularInitialization\Http\Controllers\InitializationController;

Route::prefix('api/v1')->group(function () {
    Route::post('/initialize', [InitializationController::class, 'start']);
    Route::get('/initialize/{id}', [InitializationController::class, 'status']);
    Route::post('/initialize/{id}/cancel', [InitializationController::class, 'cancel']);
});
```

### 2. WebSocket Events
```typescript
// types/websocket.ts
interface WebSocketEvents {
    'initialization.started': {
        id: string;
        components: string[];
    };
    'initialization.progress': {
        id: string;
        component: string;
        progress: number;
    };
    'initialization.completed': {
        id: string;
        status: 'success' | 'failed';
        error?: string;
    };
}

// Example usage
socket.on('initialization.progress', (data) => {
    store.dispatch('initialization/updateProgress', data);
});
```

## Database Integration

### 1. Migrations
```php
// database/migrations/create_initialization_tables.php
use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

class CreateInitializationTables extends Migration
{
    public function up()
    {
        Schema::create('initialization_status', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->string('status');
            $table->json('components');
            $table->timestamp('started_at');
            $table->timestamp('completed_at')->nullable();
            $table->timestamps();
        });

        Schema::create('initialization_components', function (Blueprint $table) {
            $table->uuid('id')->primary();
            $table->uuid('initialization_id');
            $table->string('name');
            $table->string('status');
            $table->json('metadata')->nullable();
            $table->timestamps();

            $table->foreign('initialization_id')
                  ->references('id')
                  ->on('initialization_status')
                  ->onDelete('cascade');
        });
    }
}
```

### 2. Models
```php
// src/Models/InitializationStatus.php
namespace LegalStudy\ModularInitialization\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Concerns\HasUuids;

class InitializationStatus extends Model
{
    use HasUuids;

    protected $casts = [
        'components' => 'array',
        'started_at' => 'datetime',
        'completed_at' => 'datetime'
    ];

    public function components()
    {
        return $this->hasMany(InitializationComponent::class);
    }
}
```

## Queue Integration

### 1. Job Definitions
```php
// src/Jobs/InitializeComponent.php
namespace LegalStudy\ModularInitialization\Jobs;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;

class InitializeComponent implements ShouldQueue
{
    use Dispatchable, Queueable;

    public function __construct(
        public string $componentId,
        public array $config
    ) {}

    public function handle()
    {
        $component = app('initialization')->getComponent($this->componentId);
        $component->initialize($this->config);
    }
}
```

### 2. Event Listeners
```php
// src/Listeners/HandleComponentInitialized.php
namespace LegalStudy\ModularInitialization\Listeners;

use LegalStudy\ModularInitialization\Events\ComponentInitialized;
use Illuminate\Contracts\Queue\ShouldQueue;

class HandleComponentInitialized implements ShouldQueue
{
    public function handle(ComponentInitialized $event)
    {
        // Update status
        $status = InitializationStatus::find($event->initializationId);
        $status->components = array_merge(
            $status->components,
            [$event->componentId => 'completed']
        );
        $status->save();

        // Broadcast update
        broadcast(new InitializationUpdated($status));
    }
}
```

## Cache Integration

### 1. Cache Configuration
```php
// config/cache.php
return [
    'stores' => [
        'initialization' => [
            'driver' => 'redis',
            'connection' => 'initialization',
            'prefix' => 'init:'
        ]
    ]
];
```

### 2. Cache Usage
```php
// src/Services/InitializationService.php
use Illuminate\Support\Facades\Cache;

class InitializationService
{
    public function getStatus(string $id): array
    {
        return Cache::store('initialization')
            ->remember("status:{$id}", 300, function () use ($id) {
                return InitializationStatus::with('components')
                    ->find($id)
                    ->toArray();
            });
    }
}
```

## Monitoring Integration

### 1. Metrics Collection
```php
// src/Monitoring/MetricsCollector.php
namespace LegalStudy\ModularInitialization\Monitoring;

use Prometheus\CollectorRegistry;

class MetricsCollector
{
    private $registry;
    private $counter;
    private $gauge;

    public function __construct(CollectorRegistry $registry)
    {
        $this->registry = $registry;
        $this->setupMetrics();
    }

    private function setupMetrics()
    {
        $this->counter = $this->registry->getOrRegisterCounter(
            'initialization',
            'total_initializations',
            'Total number of initializations'
        );

        $this->gauge = $this->registry->getOrRegisterGauge(
            'initialization',
            'component_status',
            'Component initialization status',
            ['component']
        );
    }
}
```

### 2. Health Checks
```php
// routes/api.php
Route::get('/health', function () {
    return response()->json([
        'status' => 'healthy',
        'services' => [
            'database' => DB::connection()->getPdo() ? 'up' : 'down',
            'cache' => Cache::store('initialization')->ping() === true,
            'queue' => Queue::size() !== null
        ]
    ]);
});
``` 