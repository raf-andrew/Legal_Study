# Laravel API Testing Checklists

## Test Structure
Each route test should include:
1. Feature test class
2. Database transactions
3. Authentication/Authorization
4. Request validation
5. Response validation
6. Error handling
7. Edge cases
8. Performance metrics

## Authentication Routes

### User Profile Route (`/api/user`)
- [ ] Feature Test Class
  - [ ] `UserProfileTest.php`
  - [ ] Uses `RefreshDatabase` trait
  - [ ] Uses `WithoutMiddleware` trait for specific tests
  - [ ] Requires authentication via Sanctum

- [ ] Basic Functionality
  - [ ] Get authenticated user profile
  - [ ] Profile data structure matches User model
  - [ ] Sensitive data filtering (password, remember_token)
  - [ ] User model relationships (if any)

- [ ] Security
  - [ ] Unauthorized access returns 401
  - [ ] Invalid token returns 401
  - [ ] Expired token returns 401
  - [ ] Rate limiting (60 requests/minute)
  - [ ] Sanctum token validation

- [ ] Performance
  - [ ] Response time < 0.5 seconds
  - [ ] Single database query
  - [ ] No N+1 queries
  - [ ] No unnecessary joins

## System Routes

### Health Check Route (`/health`)
- [ ] Feature Test Class
  - [ ] `HealthCheckTest.php`
  - [ ] Uses `RefreshDatabase` trait
  - [ ] No authentication required

- [ ] Basic Functionality
  - [ ] Returns correct JSON structure
  - [ ] Database connection check
  - [ ] Redis connection check
  - [ ] Cache connection check
  - [ ] Status reflects all services
  - [ ] Timestamp is ISO8601
  - [ ] Environment matches config
  - [ ] Version matches config

- [ ] Error Handling
  - [ ] Database down detection
  - [ ] Redis down detection
  - [ ] Cache down detection
  - [ ] Partial service failure handling

- [ ] Performance
  - [ ] Response time < 0.5 seconds
  - [ ] No database queries for status
  - [ ] Cache check is temporary
  - [ ] Concurrent requests handling
  - [ ] Load testing (100+ concurrent requests)

## Implementation Guidelines

### Database Transactions
```php
use RefreshDatabase;

protected function setUp(): void
{
    parent::setUp();
    $this->beginDatabaseTransaction();
}
```

### Authentication
```php
use Laravel\Sanctum\Sanctum;

protected function authenticate()
{
    $user = User::factory()->create();
    Sanctum::actingAs($user);
    return $user;
}
```

### Request Testing
```php
$response = $this->getJson('/api/user');

$response->assertStatus(200)
    ->assertJsonStructure([
        'id',
        'name',
        'email',
        'created_at',
        'updated_at'
    ]);
```

### Response Testing
```php
$response->assertStatus(200)
    ->assertJson([
        'status' => 'healthy'
    ])
    ->assertJsonStructure([
        'status',
        'services' => [
            'database',
            'redis',
            'cache'
        ],
        'timestamp',
        'environment',
        'version'
    ]);
```

### Error Handling
```php
$response->assertStatus(401)
    ->assertJson([
        'message' => 'Unauthenticated'
    ]);
```

### Performance Testing
```php
$start = microtime(true);
$response = $this->getJson('/api/endpoint');
$duration = microtime(true) - $start;

$this->assertLessThan(0.5, $duration);
```

## Test Reports
Each test should generate a JSON report including:
- Test name and description
- Execution time
- Status (passed/failed)
- Error details (if any)
- Performance metrics
- Coverage statistics
- Database queries executed
- Cache hits/misses
- Memory usage
- CPU usage

## Notes
- All tests must use Laravel's testing framework
- Tests should be independent and isolated
- Use factories for test data
- Implement proper authentication/authorization
- Generate detailed test reports
- Follow medical-grade certification standards
- Rate limiting: 60 requests per minute per user/IP
- Response time threshold: 0.5 seconds
- Database transactions for data integrity
- Cache utilization for performance
- Health checks for service monitoring
- Sanctum token validation
- N+1 query prevention
- Memory leak prevention
- Resource cleanup
- Concurrent request handling
- Load testing scenarios
- ISO8601 timestamp validation
- Environment configuration validation
- Version information validation
