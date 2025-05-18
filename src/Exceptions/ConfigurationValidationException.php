namespace LegalStudy\ModularInitialization\Exceptions;

class ConfigurationValidationException extends InitializationException
{
    private array $validationErrors;

    public function __construct(array $validationErrors, string $message = "", int $code = 0, ?\Throwable $previous = null)
    {
        $this->validationErrors = $validationErrors;
        $message = $message ?: "Configuration validation failed: " . implode(", ", $validationErrors);
        parent::__construct($message, $code, $previous);
    }

    public function getValidationErrors(): array
    {
        return $this->validationErrors;
    }
} 