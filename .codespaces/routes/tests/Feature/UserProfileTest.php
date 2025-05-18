<?php

namespace Tests\Feature;

use Tests\TestCase;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Laravel\Sanctum\Sanctum;

class UserProfileTest extends TestCase
{
    use RefreshDatabase;

    protected $user;

    protected function setUp(): void
    {
        parent::setUp();

        // Create a test user
        $this->user = User::factory()->create([
            'name' => 'Test User',
            'email' => 'test@example.com'
        ]);
    }

    public function test_user_can_get_own_profile()
    {
        Sanctum::actingAs($this->user);

        $response = $this->get('/api/user');

        $this->assertSuccessResponse($response, [
            'id' => $this->user->id,
            'name' => 'Test User',
            'email' => 'test@example.com'
        ]);
    }

    public function test_unauthenticated_user_cannot_get_profile()
    {
        $response = $this->get('/api/user');

        $this->assertErrorResponse($response, 401, 'Unauthenticated.');
    }

    public function test_user_can_update_own_profile()
    {
        Sanctum::actingAs($this->user);

        $response = $this->put('/api/user', [
            'name' => 'Updated Name',
            'email' => 'updated@example.com'
        ]);

        $this->assertSuccessResponse($response, [
            'id' => $this->user->id,
            'name' => 'Updated Name',
            'email' => 'updated@example.com'
        ]);

        $this->assertDatabaseHas('users', [
            'id' => $this->user->id,
            'name' => 'Updated Name',
            'email' => 'updated@example.com'
        ]);
    }

    public function test_user_cannot_update_profile_with_invalid_data()
    {
        Sanctum::actingAs($this->user);

        $response = $this->put('/api/user', [
            'name' => '',
            'email' => 'invalid-email'
        ]);

        $this->assertValidationError($response, 'name');
        $this->assertValidationError($response, 'email');
    }

    public function test_user_cannot_update_profile_with_duplicate_email()
    {
        // Create another user
        User::factory()->create([
            'email' => 'existing@example.com'
        ]);

        Sanctum::actingAs($this->user);

        $response = $this->put('/api/user', [
            'name' => 'Test User',
            'email' => 'existing@example.com'
        ]);

        $this->assertValidationError($response, 'email');
    }

    public function test_user_can_delete_own_profile()
    {
        Sanctum::actingAs($this->user);

        $response = $this->delete('/api/user');

        $this->assertSuccessResponse($response, [
            'message' => 'User deleted successfully'
        ]);

        $this->assertDatabaseMissing('users', [
            'id' => $this->user->id
        ]);
    }

    public function test_profile_endpoint_performance()
    {
        Sanctum::actingAs($this->user);

        $this->assertPerformance(function () {
            $this->get('/api/user');
        }, 0.5); // Should respond within 500ms
    }

    public function test_profile_endpoint_rate_limiting()
    {
        Sanctum::actingAs($this->user);

        // Make multiple requests in quick succession
        for ($i = 0; $i < 60; $i++) {
            $this->get('/api/user');
        }

        // The next request should be rate limited
        $response = $this->get('/api/user');
        $this->assertRateLimited($response);
    }
}
