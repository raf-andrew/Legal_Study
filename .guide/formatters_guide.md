# Formatters Guide

## Overview
The formatters module provides a flexible and extensible system for formatting output in various formats including JSON, YAML, tables, progress bars, and styled messages. This guide explains how to use each formatter and customize their behavior.

## Available Formatters

### 1. JsonFormatter
Formats data as JSON with configurable indentation and sorting.

```python
from formatters import JsonFormatter

formatter = JsonFormatter()
output = formatter.format({"name": "test", "value": 123})
```

Configuration options:
- `indent`: Number of spaces for indentation (default: 2)
- `sort_keys`: Whether to sort dictionary keys (default: True)
- `ensure_ascii`: Use ASCII encoding (default: False)

### 2. YamlFormatter
Formats data as YAML with customizable styling.

```python
from formatters import YamlFormatter

formatter = YamlFormatter()
output = formatter.format({"config": {"enabled": True}})
```

Configuration options:
- `default_flow_style`: Use flow style for collections (default: False)
- `allow_unicode`: Enable Unicode output (default: True)
- `width`: Maximum line width (default: 80)

### 3. TableFormatter
Creates formatted tables from list data.

```python
from formatters import TableFormatter

data = [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}]
formatter = TableFormatter()
output = formatter.format(data)
```

Configuration options:
- `show_header`: Display column headers (default: True)
- `show_lines`: Show table borders (default: True)
- `title_style`: Style for table title
- `header_style`: Style for column headers
- `row_styles`: List of styles to alternate between rows

### 4. ProgressFormatter
Displays progress bars and status updates.

```python
from formatters import ProgressFormatter

formatter = ProgressFormatter()
with formatter.progress() as progress:
    for i in range(100):
        progress.update(i, total=100)
```

Configuration options:
- `transient`: Clear progress bar when complete (default: True)
- `show_time`: Display elapsed time (default: True)
- `show_speed`: Show processing speed (default: True)
- `style`: Progress bar style

### 5. ErrorFormatter
Formats error messages with styling and traceback information.

```python
from formatters import ErrorFormatter

formatter = ErrorFormatter()
output = formatter.format("An error occurred", exc_info=True)
```

Configuration options:
- `style`: Error message style
- `show_traceback`: Include exception traceback (default: True)
- `show_context`: Show error context (default: True)

### 6. SuccessFormatter
Formats success messages with styling.

```python
from formatters import SuccessFormatter

formatter = SuccessFormatter()
output = formatter.format("Operation completed successfully")
```

Configuration options:
- `style`: Success message style
- `show_details`: Include additional details (default: True)

## FormatterFactory
The FormatterFactory provides a centralized way to create formatters:

```python
from formatters import FormatterFactory

factory = FormatterFactory()
formatter = factory.create("json")
output = formatter.format(data)
```

## Configuration
Formatter behavior can be customized through the `.config/formatters.yaml` file. See the configuration file for all available options.

## Themes
Custom themes can be defined in the configuration file to control:
- Syntax highlighting colors
- Status message styles
- Border and background colors

## Logging
The formatters module includes built-in logging:
- Log file: `.logs/formatters.log`
- Configurable log levels and formats
- Rotation policies for log files

## Best Practices
1. Use the FormatterFactory to create formatters
2. Configure formatters through the YAML file
3. Handle encoding consistently
4. Use appropriate formatters for different data types
5. Consider terminal capabilities when using styles

## Error Handling
Formatters include robust error handling:
- Invalid data type detection
- Encoding error handling
- Configuration validation
- Graceful fallbacks

## Performance Considerations
- Use streaming for large datasets
- Configure appropriate buffer sizes
- Monitor memory usage with large tables
- Use transient progress bars for better performance

## Contributing
To add a new formatter:
1. Create a new class inheriting from BaseFormatter
2. Implement the format() method
3. Add configuration options
4. Update the FormatterFactory
5. Add unit tests
6. Update documentation

## Support
For issues and questions:
- Check the error logs
- Review configuration
- Consult the test suite
- Submit detailed bug reports 