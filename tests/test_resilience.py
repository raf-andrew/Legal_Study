import pytest
from datetime import datetime
import random
import time
from sqlalchemy.exc import OperationalError

def test_network_resilience(client, chaos_network_conditions, performance_metrics):
    """Test API resilience under poor network conditions."""
    with chaos_network_conditions:
        start = time.time()
        response = client.get("/api/v1/health")
        duration = time.time() - start
        
        performance_metrics("api_health_check", duration)
        assert response.status_code == 200

def test_database_resilience(db, chaos_database_conditions):
    """Test application behavior under database failures."""
    success_count = 0
    total_attempts = 10
    
    for _ in range(total_attempts):
        try:
            # Attempt a simple query
            result = chaos_database_conditions.execute("SELECT 1")
            success_count += 1
        except Exception as e:
            assert "Simulated database error" in str(e)
    
    # We expect about 80% success rate (20% failure rate configured in fixture)
    assert 6 <= success_count <= 10

def test_acid_atomicity(db, acid_transaction_checker):
    """Test that transactions are atomic."""
    with acid_transaction_checker():
        # Simulate a transaction that should be atomic
        db.execute("INSERT INTO users (username, email) VALUES ('test_user', 'test@example.com')")
        # Intentionally cause an error
        with pytest.raises(Exception):
            db.execute("INSERT INTO non_existent_table VALUES (1)")
        
    # Verify the first insert was rolled back
    result = db.execute("SELECT COUNT(*) FROM users WHERE username = 'test_user'")
    assert result.scalar() == 0

def test_acid_consistency(db, acid_transaction_checker):
    """Test that transactions maintain database consistency."""
    with acid_transaction_checker():
        # Create a user and associated documents
        db.execute("""
            INSERT INTO users (username, email) 
            VALUES ('consistency_test', 'consistency@test.com')
        """)
        user_id = db.execute("SELECT id FROM users WHERE username = 'consistency_test'").scalar()
        
        # Create documents for the user
        for i in range(3):
            db.execute("""
                INSERT INTO documents (title, content, user_id) 
                VALUES (:title, :content, :user_id)
            """, {
                'title': f'Doc {i}',
                'content': f'Content {i}',
                'user_id': user_id
            })
    
    # Verify consistency - user should have exactly 3 documents
    result = db.execute("""
        SELECT COUNT(*) FROM documents 
        WHERE user_id = (SELECT id FROM users WHERE username = 'consistency_test')
    """)
    assert result.scalar() == 3

def test_acid_isolation(db, concurrent_transactions):
    """Test transaction isolation under concurrent access."""
    def update_user():
        with db.begin():
            db.execute("""
                UPDATE users 
                SET email = 'updated@test.com' 
                WHERE username = 'isolation_test'
            """)
            time.sleep(0.1)  # Simulate some work
    
    # Create test user
    db.execute("""
        INSERT INTO users (username, email) 
        VALUES ('isolation_test', 'original@test.com')
    """)
    
    # Run concurrent updates
    concurrent_transactions(update_user, times=3)
    
    # Verify final state
    result = db.execute("SELECT email FROM users WHERE username = 'isolation_test'")
    assert result.scalar() == 'updated@test.com'

def test_acid_durability(db, acid_transaction_checker, performance_metrics):
    """Test transaction durability."""
    with acid_transaction_checker():
        start_time = time.time()
        
        # Perform a write operation
        db.execute("""
            INSERT INTO users (username, email) 
            VALUES ('durability_test', 'durability@test.com')
        """)
        
        write_duration = time.time() - start_time
        performance_metrics("write_operation", write_duration)
    
    # Verify data persists after transaction
    result = db.execute("SELECT COUNT(*) FROM users WHERE username = 'durability_test'")
    assert result.scalar() == 1

def test_chaos_recovery(client, chaos_network_conditions, chaos_database_conditions, performance_metrics):
    """Test system recovery under chaotic conditions."""
    def attempt_operation():
        with chaos_network_conditions:
            try:
                response = client.post("/api/v1/users", json={
                    "username": f"chaos_user_{random.randint(1000, 9999)}",
                    "email": "chaos@test.com"
                })
                return response.status_code == 201
            except Exception:
                return False
    
    success_count = 0
    attempts = 10
    
    for i in range(attempts):
        if attempt_operation():
            success_count += 1
        time.sleep(0.5)  # Brief pause between attempts
    
    recovery_rate = success_count / attempts
    performance_metrics("chaos_recovery_rate", recovery_rate)
    
    # We expect at least 50% successful operations under chaos conditions
    assert recovery_rate >= 0.5 