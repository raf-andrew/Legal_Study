<?php

namespace Tests\Mcp\Core\Config;

use App\Mcp\Core\Config\ConfigManager;
use App\Mcp\Core\Config\ConfigManagerInterface;
use Illuminate\Support\Facades\File;
use Illuminate\Support\Facades\Storage;
use Tests\TestCase;

class ConfigManagerTest extends TestCase
{
    protected ConfigManagerInterface $configManager;
    protected string $testConfigFile;
    protected string $testStorageFile;

    protected function setUp(): void
    {
        parent::setUp();
        $this->configManager = new ConfigManager();
        $this->testConfigFile = storage_path('app/test_config.json');
        $this->testStorageFile = 'test_config.json';
    }

    protected function tearDown(): void
    {
        if (File::exists($this->testConfigFile)) {
            File::delete($this->testConfigFile);
        }
        if (Storage::exists($this->testStorageFile)) {
            Storage::delete($this->testStorageFile);
        }
        parent::tearDown();
    }

    public function test_interface_implementation(): void
    {
        $this->assertInstanceOf(ConfigManagerInterface::class, $this->configManager);
    }

    public function test_load_from_file(): void
    {
        $config = ['test' => 'value'];
        File::put($this->testConfigFile, json_encode($config));

        $this->assertTrue($this->configManager->load($this->testConfigFile));
        $this->assertEquals('value', $this->configManager->get('test'));
    }

    public function test_load_from_storage(): void
    {
        $config = ['test' => 'value'];
        Storage::put($this->testStorageFile, json_encode($config));

        $this->assertTrue($this->configManager->load($this->testStorageFile));
        $this->assertEquals('value', $this->configManager->get('test'));
    }

    public function test_load_nonexistent_file(): void
    {
        $this->assertFalse($this->configManager->load('nonexistent.json'));
    }

    public function test_save_to_file(): void
    {
        $this->configManager->set('test', 'value');
        $this->assertTrue($this->configManager->save($this->testConfigFile));

        $this->assertTrue(File::exists($this->testConfigFile));
        $content = json_decode(File::get($this->testConfigFile), true);
        $this->assertEquals(['test' => 'value'], $content);
    }

    public function test_save_to_storage(): void
    {
        $this->configManager->set('test', 'value');
        $this->assertTrue($this->configManager->save($this->testStorageFile));

        $this->assertTrue(Storage::exists($this->testStorageFile));
        $content = json_decode(Storage::get($this->testStorageFile), true);
        $this->assertEquals(['test' => 'value'], $content);
    }

    public function test_get_value(): void
    {
        $this->configManager->set('test', 'value');
        $this->assertEquals('value', $this->configManager->get('test'));
    }

    public function test_get_nested_value(): void
    {
        $this->configManager->set('test.nested', 'value');
        $this->assertEquals('value', $this->configManager->get('test.nested'));
    }

    public function test_get_default_value(): void
    {
        $this->assertEquals('default', $this->configManager->get('nonexistent', 'default'));
    }

    public function test_set_value(): void
    {
        $this->assertTrue($this->configManager->set('test', 'value'));
        $this->assertEquals('value', $this->configManager->get('test'));
    }

    public function test_set_nested_value(): void
    {
        $this->assertTrue($this->configManager->set('test.nested', 'value'));
        $this->assertEquals('value', $this->configManager->get('test.nested'));
    }

    public function test_has_value(): void
    {
        $this->configManager->set('test', 'value');
        $this->assertTrue($this->configManager->has('test'));
        $this->assertFalse($this->configManager->has('nonexistent'));
    }

    public function test_has_nested_value(): void
    {
        $this->configManager->set('test.nested', 'value');
        $this->assertTrue($this->configManager->has('test.nested'));
        $this->assertFalse($this->configManager->has('test.nonexistent'));
    }

    public function test_remove_value(): void
    {
        $this->configManager->set('test', 'value');
        $this->assertTrue($this->configManager->remove('test'));
        $this->assertFalse($this->configManager->has('test'));
    }

    public function test_remove_nested_value(): void
    {
        $this->configManager->set('test.nested', 'value');
        $this->assertTrue($this->configManager->remove('test.nested'));
        $this->assertFalse($this->configManager->has('test.nested'));
    }

    public function test_remove_nonexistent_value(): void
    {
        $this->assertFalse($this->configManager->remove('nonexistent'));
    }

    public function test_all_values(): void
    {
        $this->configManager->set('test1', 'value1');
        $this->configManager->set('test2', 'value2');
        
        $all = $this->configManager->all();
        $this->assertEquals(['test1' => 'value1', 'test2' => 'value2'], $all);
    }

    public function test_clear_values(): void
    {
        $this->configManager->set('test', 'value');
        $this->assertTrue($this->configManager->clear());
        $this->assertEmpty($this->configManager->all());
    }

    public function test_validate_configuration(): void
    {
        $schema = [
            'required' => ['required' => true, 'type' => 'string'],
            'optional' => ['type' => 'integer'],
            'enum' => ['enum' => ['value1', 'value2']],
            'min' => ['type' => 'integer', 'min' => 0],
            'max' => ['type' => 'integer', 'max' => 100],
        ];

        $this->configManager->set('required', 'test');
        $this->configManager->set('optional', 42);
        $this->configManager->set('enum', 'value1');
        $this->configManager->set('min', 10);
        $this->configManager->set('max', 90);

        $errors = $this->configManager->validate($schema);
        $this->assertEmpty($errors);
    }

    public function test_validate_configuration_errors(): void
    {
        $schema = [
            'required' => ['required' => true, 'type' => 'string'],
            'optional' => ['type' => 'integer'],
            'enum' => ['enum' => ['value1', 'value2']],
            'min' => ['type' => 'integer', 'min' => 0],
            'max' => ['type' => 'integer', 'max' => 100],
        ];

        $this->configManager->set('required', null);
        $this->configManager->set('optional', 'not an integer');
        $this->configManager->set('enum', 'invalid');
        $this->configManager->set('min', -10);
        $this->configManager->set('max', 200);

        $errors = $this->configManager->validate($schema);
        $this->assertCount(5, $errors);
    }

    public function test_environment_config(): void
    {
        $config = ['test' => 'value'];
        $this->assertTrue($this->configManager->setEnvironmentConfig('test', $config));
        $this->assertEquals($config, $this->configManager->getEnvironmentConfig('test'));
    }

    public function test_nonexistent_environment_config(): void
    {
        $this->assertEmpty($this->configManager->getEnvironmentConfig('nonexistent'));
    }
} 