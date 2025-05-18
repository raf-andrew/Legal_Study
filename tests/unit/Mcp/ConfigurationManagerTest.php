<?php

namespace Tests\Unit\Mcp;

use App\Mcp\ConfigurationManager;
use Illuminate\Support\Facades\Config;
use Tests\TestCase;

class ConfigurationManagerTest extends TestCase
{
    protected $configManager;

    protected function setUp(): void
    {
        parent::setUp();
        Config::shouldReceive('get')->with('app.env')->andReturn('local');
        $this->configManager = new ConfigurationManager();
    }

    public function testLoadConfiguration()
    {
        Config::shouldReceive('get')
            ->with('mcp', [])
            ->andReturn([
                'enabled' => true,
                'security' => [
                    'require_authentication' => false,
                ],
            ]);

        $configManager = new ConfigurationManager();
        $this->assertTrue($configManager->isEnabled());
        $this->assertFalse($configManager->get('security.require_authentication'));
    }

    public function testGetConfiguration()
    {
        $config = $this->configManager->get();
        $this->assertIsArray($config);
        $this->assertArrayHasKey('enabled', $config);
        $this->assertArrayHasKey('security', $config);
        $this->assertArrayHasKey('features', $config);
    }

    public function testGetConfigurationWithKey()
    {
        $value = $this->configManager->get('security.require_authentication');
        $this->assertTrue($value);

        $value = $this->configManager->get('non.existent.key', 'default');
        $this->assertEquals('default', $value);
    }

    public function testSetConfiguration()
    {
        $this->configManager->set('security.require_authentication', false);
        $value = $this->configManager->get('security.require_authentication');
        $this->assertFalse($value);
    }

    public function testIsEnabled()
    {
        $this->assertFalse($this->configManager->isEnabled());
        $this->configManager->set('enabled', true);
        $this->assertTrue($this->configManager->isEnabled());
    }

    public function testIsDevelopmentMode()
    {
        $this->assertTrue($this->configManager->isDevelopmentMode());
    }

    public function testIsFeatureEnabled()
    {
        $this->assertTrue($this->configManager->isFeatureEnabled('agentic'));
        $this->assertTrue($this->configManager->isFeatureEnabled('development'));
        $this->assertTrue($this->configManager->isFeatureEnabled('monitoring'));
        $this->assertFalse($this->configManager->isFeatureEnabled('non_existent_feature'));
    }

    public function testGetSecurityConfig()
    {
        $security = $this->configManager->getSecurityConfig();
        $this->assertIsArray($security);
        $this->assertArrayHasKey('require_authentication', $security);
        $this->assertArrayHasKey('allowed_origins', $security);
        $this->assertArrayHasKey('rate_limit', $security);
    }

    public function testGetServicesConfig()
    {
        $services = $this->configManager->getServicesConfig();
        $this->assertIsArray($services);
        $this->assertArrayHasKey('discovery', $services);
        $this->assertTrue($services['discovery']['enabled']);
        $this->assertEquals(60, $services['discovery']['interval']);
    }

    public function testValidateConfiguration()
    {
        $errors = $this->configManager->validateConfiguration();
        $this->assertEmpty($errors);

        // Test with invalid configuration
        $this->configManager->set('security', []);
        $errors = $this->configManager->validateConfiguration();
        $this->assertNotEmpty($errors);
        $this->assertContains('Missing required security configuration: require_authentication', $errors);
    }

    public function testSetNestedConfiguration()
    {
        $this->configManager->set('features.new_feature', true);
        $this->assertTrue($this->configManager->isFeatureEnabled('new_feature'));

        $this->configManager->set('security.new_setting.nested', 'value');
        $this->assertEquals('value', $this->configManager->get('security.new_setting.nested'));
    }

    public function testDefaultValues()
    {
        $this->assertFalse($this->configManager->get('enabled'));
        $this->assertTrue($this->configManager->get('development_mode'));
        $this->assertEquals(100, $this->configManager->get('security.rate_limit'));
        $this->assertTrue($this->configManager->get('features.agentic'));
    }

    public function testEnvironmentOverride()
    {
        Config::shouldReceive('get')->with('app.env')->andReturn('production');
        $configManager = new ConfigurationManager();
        $this->assertFalse($configManager->isDevelopmentMode());
    }
} 