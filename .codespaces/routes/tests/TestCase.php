<?php

namespace Tests;

use Illuminate\Foundation\Testing\TestCase as BaseTestCase;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\DB;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Queue;
use Illuminate\Support\Facades\Event;
use Laravel\Sanctum\Sanctum;
use Illuminate\Support\Facades\Route;
use Illuminate\Support\Facades\Config;

abstract class TestCase extends BaseTestCase
{
    use RefreshDatabase;

    protected $startTime;
    protected $coverageData = [];
    protected $performanceData = [];

    protected function setUp(): void
    {
        parent::setUp();
        $this->startTime = microtime(true);

        // Start transaction
        DB::beginTransaction();

        // Clear cache
        Cache::flush();

        // Clear queue
        Queue::after(function () {
            Queue::size();
        });

        // Fake events
        Event::fake();

        // Enable route caching for performance testing
        Config::set('app.env', 'testing');
        Route::enableRouteCache();

        // Start coverage tracking
        $this->startCoverageTracking();
    }

    protected function tearDown(): void
    {
        $this->recordCoverage();
        // Rollback transaction
        DB::rollBack();

        // Stop coverage tracking
        $this->stopCoverageTracking();

        // Clear route cache
        Route::clearResolvedInstances();
        Route::clearCache();

        parent::tearDown();
    }

    protected function recordCoverage()
    {
        $testName = $this->getName();
        $duration = microtime(true) - $this->startTime;

        $this->coverageData[$testName] = [
            'duration' => $duration,
            'memory' => memory_get_peak_usage(true),
            'queries' => DB::getQueryLog(),
            'cache_hits' => Cache::get('hits', 0),
            'cache_misses' => Cache::get('misses', 0)
        ];
    }

    protected function startCoverageTracking()
    {
        $this->coverageData = [
            'start_time' => microtime(true),
            'memory_start' => memory_get_usage(),
            'queries' => [],
            'cache_hits' => 0,
            'cache_misses' => 0
        ];

        // Enable query logging
        DB::enableQueryLog();

        // Enable cache hit/miss tracking
        Cache::enableHitMissTracking();
    }

    protected function stopCoverageTracking()
    {
        $this->coverageData['end_time'] = microtime(true);
        $this->coverageData['memory_end'] = memory_get_usage();
        $this->coverageData['queries'] = DB::getQueryLog();
        $this->coverageData['cache_hits'] = Cache::getHitCount();
        $this->coverageData['cache_misses'] = Cache::getMissCount();

        // Disable query logging
        DB::disableQueryLog();

        // Disable cache hit/miss tracking
        Cache::disableHitMissTracking();
    }

    protected function assertJsonResponse($response, $status = 200)
    {
        $response->assertStatus($status)
                ->assertHeader('Content-Type', 'application/json');
    }

    protected function assertErrorResponse($response, $status, $message = null)
    {
        $this->assertJsonResponse($response, $status);

        if ($message) {
            $response->assertJson(['message' => $message]);
        }
    }

    protected function assertSuccessResponse($response, $expectedData = null)
    {
        $this->assertJsonResponse($response);

        if ($expectedData) {
            $response->assertJson($expectedData);
        }
    }

    protected function assertValidationError($response, $field)
    {
        $this->assertJsonResponse($response, 422);
        $response->assertJsonValidationErrors([$field]);
    }

    protected function assertRateLimited($response)
    {
        $this->assertJsonResponse($response, 429);
        $response->assertJson(['message' => 'Too Many Attempts.']);
    }

    protected function assertPerformance(callable $callback, float $maxDuration)
    {
        $start = microtime(true);
        $callback();
        $duration = microtime(true) - $start;

        $this->assertLessThan(
            $maxDuration,
            $duration,
            "Operation took {$duration} seconds, which exceeds the maximum allowed duration of {$maxDuration} seconds"
        );
    }

    protected function getCoverageData()
    {
        return [
            'duration' => $this->coverageData['end_time'] - $this->coverageData['start_time'],
            'memory_usage' => $this->coverageData['memory_end'] - $this->coverageData['memory_start'],
            'queries' => count($this->coverageData['queries']),
            'cache_hits' => $this->coverageData['cache_hits'],
            'cache_misses' => $this->coverageData['cache_misses']
        ];
    }
}
