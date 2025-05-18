# Best Practices

## Configuration

### Environment Variables
- Use environment variables for sensitive data:
  ```php
  $config = [
      'host' => getenv('DB_HOST') ?: 'localhost',
      'port' => (int)(getenv('DB_PORT') ?: 3306),
      'username' => getenv('DB_USER'),
      'password' => getenv('DB_PASS')
  ];
  ```

### Input Validation
- Validate all configuration parameters:
  ```php
  if (!isset($config['host'])) {
      throw new InvalidArgumentException('Host must be specified');
  }
  if (!is_int($config['port']) || $config['port'] < 1 || $config['port'] > 65535) {
      throw new InvalidArgumentException('Invalid port number');
  }
  ```

### Default Values
- Provide sensible defaults:
  ```php
  $config = array_merge([
      'timeout' => 5,
      'retry_attempts' => 3,
      'retry_delay' => 1.0
  ], $config);
  ```

### Documentation
- Document all configuration options:
  ```php
  /**
   * Configuration options:
   * - host: Database host (required)
   * - port: Database port (default: 3306)
   * - database: Database name (required)
   * - username: Database username (required)
   * - password: Database password (required)
   * - timeout: Connection timeout in seconds (default: 5)
   * - retry_attempts: Number of retry attempts (default: 3)
   * - retry_delay: Delay between retries in seconds (default: 1.0)
   */
  ```

## Error Handling

### Error Logging
- Log all errors with context:
  ```php
  try {
      $this->connection->exec($query);
  } catch (\PDOException $e) {
      $error = sprintf(
          'Database error: %s. Query: %s',
          $e->getMessage(),
          $query
      );
      error_log($error);
      throw new RuntimeException($error, 0, $e);
  }
  ```

### Clear Messages
- Provide clear error messages:
  ```php
  if (!is_dir($path)) {
      throw new RuntimeException(
          sprintf('Path %s exists but is not a directory', $path)
      );
  }
  ```

### Retry Logic
- Implement retry logic for transient failures:
  ```php
  $attempts = 0;
  do {
      try {
          $this->connection = new PDO($dsn, $username, $password);
          return true;
      } catch (\PDOException $e) {
          $attempts++;
          if ($attempts >= $maxAttempts) {
              throw new RuntimeException(
                  'Connection failed after ' . $attempts . ' attempts'
              );
          }
          sleep($retryDelay);
      }
  } while ($attempts < $maxAttempts);
  ```

### Resource Cleanup
- Always clean up resources:
  ```php
  try {
      $stmt = $connection->prepare($query);
      $stmt->execute($params);
      return $stmt->fetch();
  } finally {
      $stmt = null;
  }
  ```

## Performance

### Operation Monitoring
- Monitor operation performance:
  ```php
  $start = microtime(true);
  try {
      $result = $operation();
      $duration = microtime(true) - $start;
      $this->monitor->recordSuccess('operation', $duration);
      return $result;
  } catch (\Exception $e) {
      $duration = microtime(true) - $start;
      $this->monitor->recordFailure('operation', $duration);
      throw $e;
  }
  ```

### Timeouts
- Set appropriate timeouts:
  ```php
  $options = [
      PDO::ATTR_TIMEOUT => $timeout,
      PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION
  ];
  $connection = new PDO($dsn, $username, $password, $options);
  ```

### Transactions
- Use transactions for atomic operations:
  ```php
  try {
      $connection->beginTransaction();
      // Perform multiple operations
      $connection->commit();
  } catch (\Exception $e) {
      $connection->rollBack();
      throw $e;
  }
  ```

### Resource Optimization
- Optimize resource usage:
  ```php
  // Use connection pooling
  $options = [
      PDO::ATTR_PERSISTENT => true
  ];
  
  // Use prepared statements
  $stmt = $connection->prepare($query);
  foreach ($data as $row) {
      $stmt->execute($row);
  }
  ```

## Security

### Input Validation
- Validate all inputs:
  ```php
  if (!filter_var($host, FILTER_VALIDATE_DOMAIN)) {
      throw new InvalidArgumentException('Invalid host');
  }
  if (!ctype_alnum($database)) {
      throw new InvalidArgumentException('Invalid database name');
  }
  ```

### Output Sanitization
- Sanitize all outputs:
  ```php
  $error = sprintf(
      'Error in %s: %s',
      htmlspecialchars($component),
      htmlspecialchars($message)
  );
  ```

### Access Control
- Implement proper access control:
  ```php
  if (!$this->hasPermission($user, 'database.write')) {
      throw new AccessDeniedException('Write access required');
  }
  ```

### Operation Monitoring
- Monitor security-related operations:
  ```php
  $this->logger->info('User {user} accessed {resource}', [
      'user' => $user->getId(),
      'resource' => $resource->getName(),
      'ip' => $_SERVER['REMOTE_ADDR']
  ]);
  ```

## Testing

### Unit Tests
- Test each component in isolation:
  ```php
  public function testValidateConfiguration(): void
  {
      $config = ['host' => 'localhost'];
      $this->assertTrue($this->initialization->validateConfiguration($config));
  }
  ```

### Integration Tests
- Test component interactions:
  ```php
  public function testDatabaseOperations(): void
  {
      $this->initialization->performInitialization();
      $connection = $this->initialization->getConnection();
      $this->assertTrue($connection->exec('CREATE TABLE test (id INT)') !== false);
  }
  ```

### Error Tests
- Test error conditions:
  ```php
  public function testInvalidConfiguration(): void
  {
      $this->expectException(InvalidArgumentException::class);
      $this->initialization->validateConfiguration([]);
  }
  ```

### Performance Tests
- Test performance requirements:
  ```php
  public function testConnectionTimeout(): void
  {
      $start = microtime(true);
      $this->initialization->testConnection();
      $duration = microtime(true) - $start;
      $this->assertLessThan(1.0, $duration);
  }
  ``` 