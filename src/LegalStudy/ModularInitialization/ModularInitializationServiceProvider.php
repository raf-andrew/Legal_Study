<?php

namespace LegalStudy\ModularInitialization;

use LegalStudy\ModularInitialization\Services\InitializationStateManager;
use LegalStudy\ModularInitialization\Services\InitializationStatus;

class ModularInitializationServiceProvider
{
    public function register(): void
    {
        // Create and register the initialization status service
        $status = new InitializationStatus();
        
        // Create and register the initialization state manager
        $manager = new InitializationStateManager($status);
        
        // Make the services available globally
        $GLOBALS['initialization_status'] = $status;
        $GLOBALS['initialization_manager'] = $manager;
    }
} 