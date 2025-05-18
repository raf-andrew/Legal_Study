"""Test utilities for unit testing."""

import json
import logging
import os
import random
import string
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

def generate_random_string(length: int = 10) -> str:
    """Generate random string.
    
    Args:
        length: Length of string to generate
        
    Returns:
        Random string
    """
    return ''.join(
        random.choices(string.ascii_letters + string.digits, k=length)
    )

def generate_random_email() -> str:
    """Generate random email address.
    
    Returns:
        Random email address
    """
    username = generate_random_string(8)
    domain = generate_random_string(6)
    tld = random.choice(['com', 'org', 'net', 'edu'])
    return f"{username}@{domain}.{tld}"

def generate_random_date(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> datetime:
    """Generate random date between start and end dates.
    
    Args:
        start_date: Start date (defaults to 1 year ago)
        end_date: End date (defaults to now)
        
    Returns:
        Random date
    """
    if not start_date:
        start_date = datetime.now() - timedelta(days=365)
    if not end_date:
        end_date = datetime.now()
    
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randint(0, days_between)
    return start_date + timedelta(days=random_days)

def generate_test_data(
    data_type: str,
    **kwargs
) -> Any:
    """Generate test data of specified type.
    
    Args:
        data_type: Type of data to generate
        **kwargs: Additional arguments for data generation
        
    Returns:
        Generated test data
    """
    generators = {
        "string": lambda: generate_random_string(
            kwargs.get("length", 10)
        ),
        "email": lambda: generate_random_email(),
        "date": lambda: generate_random_date(
            kwargs.get("start_date"),
            kwargs.get("end_date")
        ),
        "int": lambda: random.randint(
            kwargs.get("min_value", 0),
            kwargs.get("max_value", 100)
        ),
        "float": lambda: random.uniform(
            kwargs.get("min_value", 0.0),
            kwargs.get("max_value", 100.0)
        ),
        "bool": lambda: random.choice([True, False]),
        "list": lambda: [
            generate_test_data(kwargs["element_type"])
            for _ in range(kwargs.get("length", 5))
        ],
        "dict": lambda: {
            generate_random_string(): generate_test_data(kwargs["value_type"])
            for _ in range(kwargs.get("length", 5))
        }
    }
    
    if data_type not in generators:
        raise ValueError(f"Unknown data type: {data_type}")
    
    return generators[data_type]()

def compare_dicts(
    dict1: Dict[str, Any],
    dict2: Dict[str, Any],
    ignore_keys: Optional[List[str]] = None
) -> Tuple[bool, List[str]]:
    """Compare two dictionaries.
    
    Args:
        dict1: First dictionary
        dict2: Second dictionary
        ignore_keys: Keys to ignore in comparison
        
    Returns:
        Tuple of (is_equal, differences)
    """
    ignore_keys = ignore_keys or []
    differences = []
    
    # Get all keys from both dictionaries
    all_keys = set(dict1.keys()) | set(dict2.keys())
    
    for key in all_keys:
        if key in ignore_keys:
            continue
        
        if key not in dict1:
            differences.append(f"Key '{key}' missing in first dict")
            continue
        
        if key not in dict2:
            differences.append(f"Key '{key}' missing in second dict")
            continue
        
        if dict1[key] != dict2[key]:
            differences.append(
                f"Value mismatch for key '{key}': "
                f"{dict1[key]} != {dict2[key]}"
            )
    
    return len(differences) == 0, differences

def wait_for_condition(
    condition: callable,
    timeout: float = 5.0,
    interval: float = 0.1,
    error_message: str = "Condition not met"
) -> None:
    """Wait for condition to be true.
    
    Args:
        condition: Function that returns bool
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds
        error_message: Message to show if timeout occurs
        
    Raises:
        TimeoutError: If condition not met within timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if condition():
            return
        time.sleep(interval)
    raise TimeoutError(error_message)

def create_temp_file(
    content: str,
    prefix: Optional[str] = None,
    suffix: Optional[str] = None,
    dir: Optional[str] = None
) -> str:
    """Create temporary file with content.
    
    Args:
        content: File content
        prefix: File name prefix
        suffix: File name suffix
        dir: Directory to create file in
        
    Returns:
        Path to created file
    """
    import tempfile
    
    with tempfile.NamedTemporaryFile(
        mode='w',
        prefix=prefix,
        suffix=suffix,
        dir=dir,
        delete=False
    ) as f:
        f.write(content)
        return f.name

def load_json_file(path: str) -> Dict[str, Any]:
    """Load JSON file.
    
    Args:
        path: Path to JSON file
        
    Returns:
        Loaded JSON data
        
    Raises:
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If file is not valid JSON
    """
    with open(path) as f:
        return json.load(f)

def save_json_file(
    data: Dict[str, Any],
    path: str,
    indent: int = 4
) -> None:
    """Save data to JSON file.
    
    Args:
        data: Data to save
        path: Path to save to
        indent: JSON indentation
    """
    with open(path, 'w') as f:
        json.dump(data, f, indent=indent)

def setup_test_logger(
    name: str,
    level: str = "DEBUG"
) -> logging.Logger:
    """Set up logger for testing.
    
    Args:
        name: Logger name
        level: Log level
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add console handler
    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    )
    logger.addHandler(handler)
    
    return logger

def mock_environment_variables(
    variables: Dict[str, str]
) -> Dict[str, Optional[str]]:
    """Mock environment variables.
    
    Args:
        variables: Dictionary of variables to set
        
    Returns:
        Dictionary of original values
    """
    original_values = {}
    
    for key, value in variables.items():
        original_values[key] = os.environ.get(key)
        os.environ[key] = value
    
    return original_values

def restore_environment_variables(
    original_values: Dict[str, Optional[str]]
) -> None:
    """Restore environment variables.
    
    Args:
        original_values: Dictionary of original values
    """
    for key, value in original_values.items():
        if value is None:
            if key in os.environ:
                del os.environ[key]
        else:
            os.environ[key] = value

def assert_dict_subset(
    subset: Dict[str, Any],
    full_dict: Dict[str, Any]
) -> None:
    """Assert that one dict is a subset of another.
    
    Args:
        subset: Expected subset dictionary
        full_dict: Full dictionary to check against
        
    Raises:
        AssertionError: If subset is not contained in full_dict
    """
    for key, value in subset.items():
        assert key in full_dict, f"Key '{key}' not found in full dictionary"
        assert full_dict[key] == value, \
            f"Value mismatch for key '{key}': {value} != {full_dict[key]}"

def assert_list_equal_unordered(
    list1: List[Any],
    list2: List[Any]
) -> None:
    """Assert that two lists are equal ignoring order.
    
    Args:
        list1: First list
        list2: Second list
        
    Raises:
        AssertionError: If lists are not equal
    """
    assert len(list1) == len(list2), \
        f"Lists have different lengths: {len(list1)} != {len(list2)}"
    assert sorted(list1) == sorted(list2), \
        "Lists contain different elements"

def assert_datetime_almost_equal(
    dt1: datetime,
    dt2: datetime,
    delta: timedelta = timedelta(seconds=1)
) -> None:
    """Assert that two datetimes are almost equal.
    
    Args:
        dt1: First datetime
        dt2: Second datetime
        delta: Maximum allowed difference
        
    Raises:
        AssertionError: If datetimes differ by more than delta
    """
    difference = abs(dt1 - dt2)
    assert difference <= delta, \
        f"Datetimes differ by {difference}, more than allowed {delta}" 