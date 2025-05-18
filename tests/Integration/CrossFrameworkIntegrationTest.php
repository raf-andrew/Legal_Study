<?php

namespace Tests\Integration;

use LegalStudy\ModularInitialization\Initializers\CacheInitialization;
use LegalStudy\ModularInitialization\Initializers\DatabaseInitialization;
use LegalStudy\ModularInitialization\Initializers\FileSystemInitialization;
use PHPUnit\Framework\TestCase;

class CrossFrameworkIntegrationTest extends TestCase
{
    private CacheInitialization $cacheInit;
    private DatabaseInitialization $dbInit;
    private FileSystemInitialization $fsInit;

    protected function setUp(): void
    {
        $this->cacheInit = new CacheInitialization();
        $this->dbInit = new DatabaseInitialization();
        $this->fsInit = new FileSystemInitialization();
    }

    public function testCacheAndDatabaseIntegration(): void
    {
        // Configure cache
        $cacheConfig = [
            'host' => 'localhost',
            'port' => 6379,
            'timeout' => 5
        ];

        // Configure database
        $dbConfig = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];

        // Initialize cache
        $this->cacheInit->validateConfiguration($cacheConfig);
        $this->assertTrue($this->cacheInit->testConnection());
        $this->cacheInit->performInitialization();

        // Initialize database
        $this->dbInit->validateConfiguration($dbConfig);
        $this->assertTrue($this->dbInit->testConnection());
        $this->dbInit->performInitialization();

        // Test integration
        $cache = $this->cacheInit->getConnection();
        $db = $this->dbInit->getConnection();

        // Store database query result in cache
        $stmt = $db->prepare('SELECT 1');
        $stmt->execute();
        $result = $stmt->fetch(\PDO::FETCH_ASSOC);
        
        $cache->set('test_key', json_encode($result));
        $this->assertEquals(json_encode($result), $cache->get('test_key'));
    }

    public function testFileSystemAndDatabaseIntegration(): void
    {
        // Configure filesystem
        $fsConfig = [
            'base_path' => sys_get_temp_dir(),
            'permissions' => 0755,
            'required_dirs' => ['test_dir']
        ];

        // Configure database
        $dbConfig = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];

        // Initialize filesystem
        $this->fsInit->validateConfiguration($fsConfig);
        $this->assertTrue($this->fsInit->testConnection());
        $this->fsInit->performInitialization();

        // Initialize database
        $this->dbInit->validateConfiguration($dbConfig);
        $this->assertTrue($this->dbInit->testConnection());
        $this->dbInit->performInitialization();

        // Test integration
        $db = $this->dbInit->getConnection();
        
        // Create test table
        $db->exec('CREATE TABLE IF NOT EXISTS test_files (id INT PRIMARY KEY, path VARCHAR(255))');
        
        // Store file path in database
        $stmt = $db->prepare('INSERT INTO test_files (id, path) VALUES (?, ?)');
        $stmt->execute([1, $fsConfig['base_path'] . '/test_dir']);
        
        // Verify integration
        $stmt = $db->prepare('SELECT path FROM test_files WHERE id = ?');
        $stmt->execute([1]);
        $result = $stmt->fetch(\PDO::FETCH_ASSOC);
        
        $this->assertTrue(is_dir($result['path']));
    }

    public function testErrorPropagation(): void
    {
        // Configure with invalid settings
        $cacheConfig = ['host' => 'invalid_host'];
        $dbConfig = ['host' => 'invalid_host'];
        $fsConfig = ['base_path' => '/invalid/path'];

        // Test error handling
        $this->cacheInit->validateConfiguration($cacheConfig);
        $this->dbInit->validateConfiguration($dbConfig);
        $this->fsInit->validateConfiguration($fsConfig);

        $this->assertFalse($this->cacheInit->testConnection());
        $this->assertFalse($this->dbInit->testConnection());
        $this->assertFalse($this->fsInit->testConnection());

        // Verify error messages
        $this->assertNotEmpty($this->cacheInit->getStatus()->getErrors());
        $this->assertNotEmpty($this->dbInit->getStatus()->getErrors());
        $this->assertNotEmpty($this->fsInit->getStatus()->getErrors());
    }

    public function testResourceManagement(): void
    {
        // Configure all frameworks
        $cacheConfig = ['host' => 'localhost', 'port' => 6379];
        $dbConfig = [
            'host' => 'localhost',
            'port' => 3306,
            'database' => 'test_db',
            'username' => 'test_user',
            'password' => 'test_pass'
        ];
        $fsConfig = [
            'base_path' => sys_get_temp_dir(),
            'permissions' => 0755
        ];

        // Initialize all frameworks
        $this->cacheInit->validateConfiguration($cacheConfig);
        $this->dbInit->validateConfiguration($dbConfig);
        $this->fsInit->validateConfiguration($fsConfig);

        $this->assertTrue($this->cacheInit->testConnection());
        $this->assertTrue($this->dbInit->testConnection());
        $this->assertTrue($this->fsInit->testConnection());

        $this->cacheInit->performInitialization();
        $this->dbInit->performInitialization();
        $this->fsInit->performInitialization();

        // Verify resource cleanup
        $this->assertNotNull($this->cacheInit->getConnection());
        $this->assertNotNull($this->dbInit->getConnection());
        $this->assertTrue(is_dir($fsConfig['base_path']));
    }

    protected function tearDown(): void
    {
        // Cleanup
        if ($this->dbInit->getStatus()->isInitialized()) {
            $db = $this->dbInit->getConnection();
            $db->exec('DROP TABLE IF EXISTS test_files');
        }
    }
} 