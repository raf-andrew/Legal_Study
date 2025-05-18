<?php

namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Redis;
use Illuminate\Support\Facades\Cache;

class HealthController extends Controller
{
    public function check(): JsonResponse
    {
        $services = [
            'database' => $this->checkDatabase(),
            'redis' => $this->checkRedis(),
            'cache' => $this->checkCache()
        ];

        $status = !in_array(false, $services) ? 'healthy' : 'unhealthy';

        return response()->json([
            'status' => $status,
            'services' => $services,
            'timestamp' => now()->toIso8601String(),
            'environment' => config('app.env'),
            'version' => config('app.version')
        ]);
    }

    private function checkDatabase(): bool
    {
        try {
            DB::connection()->getPdo();
            return true;
        } catch (\Exception $e) {
            return false;
        }
    }

    private function checkRedis(): bool
    {
        try {
            Redis::ping();
            return true;
        } catch (\Exception $e) {
            return false;
        }
    }

    private function checkCache(): bool
    {
        try {
            Cache::put('health_check', true, 1);
            return Cache::get('health_check') === true;
        } catch (\Exception $e) {
            return false;
        }
    }
}
