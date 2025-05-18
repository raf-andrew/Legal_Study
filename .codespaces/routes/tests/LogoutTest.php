<?php

namespace Tests\Feature;

use Tests\TestCase;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Hash;
use Laravel\Sanctum\Sanctum;

class LogoutTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
    }

    /** @test */
    public function authenticated_user_can_logout()
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123')
        ]);

        Sanctum::actingAs($user);

        $response = $this->postJson('/api/auth/logout');

        $response->assertStatus(200)
            ->assertJson([
                'message' => 'Successfully logged out'
            ]);

        // Verify token is invalidated
        $this->assertDatabaseMissing('personal_access_tokens', [
            'tokenable_id' => $user->id,
            'tokenable_type' => User::class
        ]);
    }

    /** @test */
    public function unauthenticated_user_cannot_logout()
    {
        $response = $this->postJson('/api/auth/logout');

        $response->assertStatus(401)
            ->assertJson([
                'message' => 'Unauthenticated'
            ]);
    }

    /** @test */
    public function logout_invalidates_all_user_tokens()
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123')
        ]);

        // Create multiple tokens for the user
        Sanctum::actingAs($user);
        $token1 = $user->createToken('test-token-1')->plainTextToken;
        $token2 = $user->createToken('test-token-2')->plainTextToken;

        $response = $this->postJson('/api/auth/logout');

        $response->assertStatus(200);

        // Verify all tokens are invalidated
        $this->assertDatabaseMissing('personal_access_tokens', [
            'tokenable_id' => $user->id,
            'tokenable_type' => User::class
        ]);

        // Verify tokens can't be used
        $this->withHeaders([
            'Authorization' => 'Bearer ' . $token1
        ])->getJson('/api/user')->assertStatus(401);

        $this->withHeaders([
            'Authorization' => 'Bearer ' . $token2
        ])->getJson('/api/user')->assertStatus(401);
    }

    /** @test */
    public function logout_cleans_up_user_sessions()
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123')
        ]);

        Sanctum::actingAs($user);

        // Create a session
        $this->withSession(['user_id' => $user->id])
            ->getJson('/api/user');

        $response = $this->postJson('/api/auth/logout');

        $response->assertStatus(200);

        // Verify session is cleared
        $this->withSession(['user_id' => $user->id])
            ->getJson('/api/user')
            ->assertStatus(401);
    }

    /** @test */
    public function logout_handles_invalid_token()
    {
        $response = $this->withHeaders([
            'Authorization' => 'Bearer invalid-token'
        ])->postJson('/api/auth/logout');

        $response->assertStatus(401)
            ->assertJson([
                'message' => 'Unauthenticated'
            ]);
    }

    /** @test */
    public function logout_is_rate_limited()
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123')
        ]);

        Sanctum::actingAs($user);

        for ($i = 0; $i < 60; $i++) {
            $response = $this->postJson('/api/auth/logout');
        }

        $response = $this->postJson('/api/auth/logout');

        $response->assertStatus(429)
            ->assertJson([
                'message' => 'Too many requests'
            ]);
    }

    /** @test */
    public function logout_performance_is_within_limits()
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123')
        ]);

        Sanctum::actingAs($user);

        $start = microtime(true);

        $response = $this->postJson('/api/auth/logout');

        $duration = microtime(true) - $start;

        $response->assertStatus(200);
        $this->assertLessThan(0.5, $duration, 'Logout response time exceeded 0.5 seconds');
    }

    /** @test */
    public function logout_handles_database_errors()
    {
        $user = User::factory()->create([
            'email' => 'test@example.com',
            'password' => Hash::make('password123')
        ]);

        Sanctum::actingAs($user);

        // Simulate database connection error
        $this->mock(\Illuminate\Database\Connection::class)
            ->shouldReceive('table')
            ->andThrow(new \Exception('Database connection error'));

        $response = $this->postJson('/api/auth/logout');

        $response->assertStatus(500)
            ->assertJson([
                'message' => 'Internal server error'
            ]);
    }
}
