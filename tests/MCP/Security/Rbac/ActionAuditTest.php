<?php

namespace Tests\Mcp\Security\Rbac;

use Mcp\Security\Rbac\ActionAudit;
use PHPUnit\Framework\TestCase;

class ActionAuditTest extends TestCase
{
    private ActionAudit $actionAudit;

    protected function setUp(): void
    {
        $this->actionAudit = new ActionAudit(5); // Small max log size for testing
    }

    public function testLogAction(): void
    {
        $this->actionAudit->logAction(
            'test_role',
            'test_action',
            ['param' => 'value'],
            'success',
            null
        );

        $log = $this->actionAudit->getAuditLog();
        $this->assertCount(1, $log);
        $this->assertEquals('test_role', $log[0]['role']);
        $this->assertEquals('test_action', $log[0]['action']);
        $this->assertEquals(['param' => 'value'], $log[0]['details']);
        $this->assertEquals('success', $log[0]['result']);
        $this->assertNull($log[0]['error']);
    }

    public function testLogSizeLimit(): void
    {
        for ($i = 0; $i < 10; $i++) {
            $this->actionAudit->logAction(
                'test_role',
                "action_{$i}",
                [],
                'success'
            );
        }

        $log = $this->actionAudit->getAuditLog();
        $this->assertCount(5, $log); // Should be limited to max size
        $this->assertEquals('action_5', $log[0]['action']); // First entry should be action_5
        $this->assertEquals('action_9', $log[4]['action']); // Last entry should be action_9
    }

    public function testGetAuditLogWithFilters(): void
    {
        $this->actionAudit->logAction('role1', 'action1', [], 'success');
        $this->actionAudit->logAction('role2', 'action2', [], 'success');
        $this->actionAudit->logAction('role1', 'action2', [], 'success');

        // Filter by role
        $log = $this->actionAudit->getAuditLog('role1');
        $this->assertCount(2, $log);
        foreach ($log as $entry) {
            $this->assertEquals('role1', $entry['role']);
        }

        // Filter by action
        $log = $this->actionAudit->getAuditLog(null, 'action2');
        $this->assertCount(2, $log);
        foreach ($log as $entry) {
            $this->assertEquals('action2', $entry['action']);
        }

        // Filter by both
        $log = $this->actionAudit->getAuditLog('role1', 'action2');
        $this->assertCount(1, $log);
        $this->assertEquals('role1', $log[0]['role']);
        $this->assertEquals('action2', $log[0]['action']);
    }

    public function testGetAuditLogWithTimeFilters(): void
    {
        $startTime = microtime(true);
        $this->actionAudit->logAction('test_role', 'action1', [], 'success');
        $middleTime = microtime(true);
        $this->actionAudit->logAction('test_role', 'action2', [], 'success');
        $endTime = microtime(true);

        // Filter by start time
        $log = $this->actionAudit->getAuditLog(null, null, $middleTime);
        $this->assertCount(1, $log);
        $this->assertEquals('action2', $log[0]['action']);

        // Filter by end time
        $log = $this->actionAudit->getAuditLog(null, null, null, $middleTime);
        $this->assertCount(1, $log);
        $this->assertEquals('action1', $log[0]['action']);

        // Filter by both
        $log = $this->actionAudit->getAuditLog(null, null, $startTime, $endTime);
        $this->assertCount(2, $log);
    }

    public function testClearAuditLog(): void
    {
        $this->actionAudit->logAction('test_role', 'test_action', [], 'success');
        $this->actionAudit->clearAuditLog();
        $this->assertEmpty($this->actionAudit->getAuditLog());
    }

    public function testSetMaxLogSize(): void
    {
        $this->actionAudit->setMaxLogSize(3);
        for ($i = 0; $i < 5; $i++) {
            $this->actionAudit->logAction('test_role', "action_{$i}", [], 'success');
        }
        $this->assertCount(3, $this->actionAudit->getAuditLog());
    }
} 