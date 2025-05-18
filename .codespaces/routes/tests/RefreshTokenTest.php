<?php

namespace Tests\Feature;

use Tests\TestCase;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;
use Laravel\Sanctum\Sanctum;

class RefreshTokenTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
    }

    /** @test */
    public function user_can_refresh_token_with_valid_refresh_token()
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123')
        ]);

        // Login to get initial tokens
        $loginResponse = $this->postJson('/api/auth/login', [
            'email' => 'test@example.com',
            'password' => 'password123'
        ]);

        $refreshToken = $loginResponse->json('refresh_token');

        $response = $this->postJson('/api/auth/refresh', [
            'refresh_token' => $refreshToken
        ]);

        $response->assertStatus(200)
            ->assertJsonStructure([
                'token',
                'refresh_token'
            ]);

        // Verify new token works
        $newToken = $response->json('token');
        $this->withHeaders([
            'Authorization' => 'Bearer ' . $newToken
        ])->getJson('/api/user')->assertStatus(200);
    }

    /** @test */
    public function refresh_token_requires_refresh_token()
    {
        $response = $this->postJson('/api/auth/refresh', []);

        $response->assertStatus(422)
            ->assertJsonValidationErrors(['refresh_token']);
    }

    /** @test */
    public function refresh_token_fails_with_invalid_token()
    {
        $response = $this->postJson('/api/auth/refresh', [
            'refresh_token' => 'invalid-token'
        ]);

        $response->assertStatus(401)
            ->assertJson([
                'message' => 'Invalid refresh token'
            ]);
    }

    /** @test */
    public function refresh_token_fails_with_expired_token()
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123')
        ]);

        // Create an expired refresh token
        $expiredToken = $user->createToken('refresh-token', ['*'], now()->subDay())->plainTextToken;

        $response = $this->postJson('/api/auth/refresh', [
            'refresh_token' => $expiredToken
        ]);

        $response->assertStatus(401)
            ->assertJson([
                'message' => 'Refresh token has expired'
            ]);
    }

    /** @test */
    public function refresh_token_invalidates_old_token()
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123')
        ]);

        // Login to get initial tokens
        $loginResponse = $this->postJson('/api/auth/login', [
            'email' => 'test@example.com',
            'password' => 'password123'
        ]);

        $oldToken = $loginResponse->json('token');
        $refreshToken = $loginResponse->json('refresh_token');

        $response = $this->postJson('/api/auth/refresh', [
            'refresh_token' => $refreshToken
        ]);

        $response->assertStatus(200);

        // Verify old token is invalidated
        $this->withHeaders([
            'Authorization' => 'Bearer ' . $oldToken
        ])->getJson('/api/user')->assertStatus(401);
    }

    /** @test */
    public function refresh_token_is_rate_limited()
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123')
        ]);

        // Login to get refresh token
        $loginResponse = $this->postJson('/api/auth/login', [
            'email' => 'test@example.com',
            'password' => 'password123'
        ]);

        $refreshToken = $loginResponse->json('refresh_token');

        for ($i = 0; $i < 60; $i++) {
            $response = $this->postJson('/api/auth/refresh', [
                'refresh_token' => $refreshToken
            ]);
        }

        $response = $this->postJson('/api/auth/refresh', [
            'refresh_token' => $refreshToken
        ]);

        $response->assertStatus(429)
            ->assertJson([
                'message' => 'Too many requests'
            ]);
    }

    /** @test */
    public function refresh_token_performance_is_within_limits()
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123')
        ]);

        // Login to get refresh token
        $loginResponse = $this->postJson('/api/auth/login', [
            'email' => 'test@example.com',
            'password' => 'password123'
        ]);

        $refreshToken = $loginResponse->json('refresh_token');

        $start = microtime(true);

        $response = $this->postJson('/api/auth/refresh', [
            'refresh_token' => $refreshToken
        ]);

        $duration = microtime(true) - $start;

        $response->assertStatus(200);
        $this->assertLessThan(0.5, $duration, 'Token refresh response time exceeded 0.5 seconds');
    }

    /** @test */
    public function refresh_token_handles_database_errors()
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123')
        ]);

        // Login to get refresh token
        $loginResponse = $this->postJson('/api/auth/login', [
            'email' => 'test@example.com',
            'password' => 'password123'
        ]);

        $refreshToken = $loginResponse->json('refresh_token');

        // Simulate database connection error
        $this->mock(\Illuminate\Database\Connection::class)
            ->shouldReceive('table')
            ->andThrow(new \Exception('Database connection error'));

        $response = $this->postJson('/api/auth/refresh', [
            'refresh_token' => $refreshToken
        ]);

        $response->assertStatus(500)
            ->assertJson([
                'message' => 'Internal server error'
            ]);
    }

    /** @test */
    public function refresh_token_handles_concurrent_requests()
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123')
        ]);

        // Login to get refresh token
        $loginResponse = $this->postJson('/api/auth/login', [
            'email' => 'test@example.com',
            'password' => 'password123'
        ]);

        $refreshToken = $loginResponse->json('refresh_token');

        $promises = [];
        for ($i = 0; $i < 5; $i++) {
            $promises[] = $this->postJson('/api/auth/refresh', [
                'refresh_token' => $refreshToken
            ]);
        }

        foreach ($promises as $response) {
            $response->assertStatus(200)
                ->assertJsonStructure([
                    'token',
                    'refresh_token'
                ]);
        }
    }
}
