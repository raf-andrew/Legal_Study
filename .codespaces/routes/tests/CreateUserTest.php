<?php

namespace Tests\Feature;

use Tests\TestCase;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Foundation\Testing\WithoutMiddleware;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\Mail;
use Illuminate\Support\Facades\Event;
use App\Events\UserCreated;
use App\Mail\WelcomeEmail;

class CreateUserTest extends TestCase
{
    use RefreshDatabase;

    protected function setUp(): void
    {
        parent::setUp();
        Mail::fake();
        Event::fake();
    }

    /** @test */
    public function user_can_be_created_with_valid_data()
    {
        $userData = [
            'name' => 'Test User',
            'email' => 'test@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!'
        ];

        $response = $this->postJson('/api/users', $userData);

        $response->assertStatus(201)
            ->assertJsonStructure([
                'user' => [
                    'id',
                    'name',
                    'email',
                    'created_at'
                ],
                'token',
                'refresh_token'
            ]);

        $this->assertDatabaseHas('users', [
            'email' => 'test@example.com',
            'name' => 'Test User'
        ]);

        Mail::assertSent(WelcomeEmail::class, function ($mail) {
            return $mail->hasTo('test@example.com');
        });

        Event::assertDispatched(UserCreated::class);
    }

    /** @test */
    public function user_creation_requires_all_fields()
    {
        $response = $this->postJson('/api/users', []);

        $response->assertStatus(422)
            ->assertJsonValidationErrors(['name', 'email', 'password']);
    }

    /** @test */
    public function user_creation_validates_email_format()
    {
        $response = $this->postJson('/api/users', [
            'name' => 'Test User',
            'email' => 'invalid-email',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!'
        ]);

        $response->assertStatus(422)
            ->assertJsonValidationErrors(['email']);
    }

    /** @test */
    public function user_creation_validates_password_strength()
    {
        $response = $this->postJson('/api/users', [
            'name' => 'Test User',
            'email' => 'test@example.com',
            'password' => 'weak',
            'password_confirmation' => 'weak'
        ]);

        $response->assertStatus(422)
            ->assertJsonValidationErrors(['password']);
    }

    /** @test */
    public function user_creation_validates_password_confirmation()
    {
        $response = $this->postJson('/api/users', [
            'name' => 'Test User',
            'email' => 'test@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'DifferentPassword123!'
        ]);

        $response->assertStatus(422)
            ->assertJsonValidationErrors(['password']);
    }

    /** @test */
    public function user_creation_prevents_duplicate_emails()
    {
        User::factory()->create([
            'email' => 'test@example.com'
        ]);

        $response = $this->postJson('/api/users', [
            'name' => 'Test User',
            'email' => 'test@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!'
        ]);

        $response->assertStatus(409)
            ->assertJson([
                'message' => 'Email already exists'
            ]);
    }

    /** @test */
    public function user_creation_hashes_password()
    {
        $userData = [
            'name' => 'Test User',
            'email' => 'test@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!'
        ];

        $this->postJson('/api/users', $userData);

        $this->assertDatabaseMissing('users', [
            'email' => 'test@example.com',
            'password' => 'Password123!'
        ]);

        $user = User::where('email', 'test@example.com')->first();
        $this->assertTrue(Hash::check('Password123!', $user->password));
    }

    /** @test */
    public function user_creation_sends_welcome_email()
    {
        $userData = [
            'name' => 'Test User',
            'email' => 'test@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!'
        ];

        $this->postJson('/api/users', $userData);

        Mail::assertSent(WelcomeEmail::class, function ($mail) {
            return $mail->hasTo('test@example.com') &&
                   $mail->user->name === 'Test User';
        });
    }

    /** @test */
    public function user_creation_dispatches_event()
    {
        $userData = [
            'name' => 'Test User',
            'email' => 'test@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!'
        ];

        $this->postJson('/api/users', $userData);

        Event::assertDispatched(UserCreated::class, function ($event) {
            return $event->user->email === 'test@example.com';
        });
    }

    /** @test */
    public function user_creation_is_rate_limited()
    {
        for ($i = 0; $i < 5; $i++) {
            $response = $this->postJson('/api/users', [
                'name' => "Test User $i",
                'email' => "test$i@example.com",
                'password' => 'Password123!',
                'password_confirmation' => 'Password123!'
            ]);
        }

        $response = $this->postJson('/api/users', [
            'name' => 'Test User 6',
            'email' => 'test6@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!'
        ]);

        $response->assertStatus(429)
            ->assertJson([
                'message' => 'Too many requests'
            ]);
    }

    /** @test */
    public function user_creation_performance_is_within_limits()
    {
        $userData = [
            'name' => 'Test User',
            'email' => 'test@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!'
        ];

        $start = microtime(true);

        $response = $this->postJson('/api/users', $userData);

        $duration = microtime(true) - $start;

        $response->assertStatus(201);
        $this->assertLessThan(1.0, $duration, 'User creation response time exceeded 1 second');
    }

    /** @test */
    public function user_creation_handles_database_errors()
    {
        // Simulate database connection error
        $this->mock(\Illuminate\Database\Connection::class)
            ->shouldReceive('table')
            ->andThrow(new \Exception('Database connection error'));

        $response = $this->postJson('/api/users', [
            'name' => 'Test User',
            'email' => 'test@example.com',
            'password' => 'Password123!',
            'password_confirmation' => 'Password123!'
        ]);

        $response->assertStatus(500)
            ->assertJson([
                'message' => 'Internal server error'
            ]);
    }
}
