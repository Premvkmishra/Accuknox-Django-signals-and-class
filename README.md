# AccuKnox Django Assignment

A professional Django project investigating Django signal behavior and implementing custom Python classes with the iterator protocol.

## Project Overview

This project provides a comprehensive investigation into Django's signal system, answering three fundamental questions about signal execution behavior:

1. **Synchronous vs Asynchronous Execution**: Do Django signals execute synchronously or asynchronously?
2. **Thread Execution Context**: Do Django signals run in the same thread as the caller?
3. **Transaction Behavior**: Do Django signals run in the same database transaction as the caller?

Additionally, the project implements a professional `Rectangle` class that demonstrates Python's iterator protocol.

## Technology Stack

- **Python**: 3.12+
- **Django**: 5.0.6
- **Django REST Framework**: 3.15.1
- **Database**: SQLite
- **Testing**: pytest + pytest-django + Django TestCase
- **Code Quality**: black, flake8, mypy, django-stubs
- **Logging**: python-json-logger (structured logging)

## Project Structure

```
accuknox_assignment/
│
├── README.md
├── requirements.txt
├── manage.py
├── pytest.ini
├── .gitignore
│
├── accuknox_assignment/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── core/
│   ├── __init__.py
│   ├── apps.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── signals.py
│   ├── rectangle.py
│   └── tests/
│       ├── __init__.py
│       ├── test_sync.py
│       ├── test_thread.py
│       ├── test_transaction.py
│       └── test_rectangle.py
│
└── templates/
    └── index.html
```

## Setup Instructions

### Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd accuknox_assignment
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run database migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (optional, for admin access):
   ```bash
   python manage.py createsuperuser
   ```

## Running the Project

### Start the Development Server

```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

### Access API Endpoints

The following API endpoints are available for signal investigation:

- **Synchronization Test**: `GET /api/signal/sync/`
- **Threading Test**: `GET /api/signal/thread/`
- **Transaction Test**: `GET /api/signal/transaction/`
- **Transaction Commit Test**: `GET /api/signal/transaction/commit/`

Example usage:
```bash
curl http://localhost:8000/api/signal/sync/
curl http://localhost:8000/api/signal/thread/
curl http://localhost:8000/api/signal/transaction/
```

## Running Tests

### Using pytest

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov-report=html

# Run specific test file
pytest core/tests/test_sync.py

# Run specific test
pytest core/tests/test_sync.py::SignalSynchronizationTests::test_signal_execution_is_synchronous

# Run with verbose output
pytest -v
```

### Using Django's test runner

```bash
# Run all tests
python manage.py test

# Run specific app
python manage.py test core

# Run specific test file
python manage.py test core.tests.test_sync

# Run specific test class
python manage.py test core.tests.test_sync.SignalSynchronizationTests

# Run with verbose output
python manage.py test --verbosity=2
```

## Assignment Questions & Findings

### Question 1: Are Django signals executed synchronously or asynchronously?

#### Hypothesis
Django signals are executed synchronously by default. The caller waits for the signal handler to complete before continuing execution.

#### Experiment
1. Created a `SignalTestModel` with a `post_save` signal handler
2. The signal handler includes an intentional delay (e.g., 2 seconds)
3. Measured the total execution time when creating an instance
4. Compared total execution time with the signal delay

#### Methodology
```python
# Create instance with 2-second delay in signal
start_time = time.time()
instance = SignalTestModel.objects.create(
    name="sync_test",
    signal_delay_seconds=2.0,
)
total_time = time.time() - start_time
```

#### Results
- **Total execution time**: ~2.0 seconds
- **Signal execution time**: ~2.0 seconds
- **Signal executed**: True
- **Caller waited for signal**: Yes

#### Conclusion
**Django signals are executed synchronously by default.**

The total execution time (2.0s) is equal to the signal delay (2.0s), proving that the caller waits for the signal handler to complete before continuing. If signals were asynchronous, the total execution time would be significantly less than the signal delay.

**Evidence**:
- Test: `core/tests/test_sync.py::SignalSynchronizationTests::test_signal_execution_is_synchronous`
- API Endpoint: `GET /api/signal/sync/`

---

### Question 2: Do Django signals run in the same thread as the caller?

#### Hypothesis
Django signals run in the same thread as the caller. Signal handlers execute in the thread that triggered the signal.

#### Experiment
1. Captured the caller's thread ID using `threading.get_ident()`
2. Created a `SignalTestModel` instance
3. The signal handler captured its thread ID
4. Compared the caller and signal thread IDs

#### Methodology
```python
caller_thread_id = str(threading.get_ident())
instance = SignalTestModel.objects.create(
    name="thread_test",
    caller_thread_id=caller_thread_id,
)
# Signal handler records: signal_thread_id = str(threading.get_ident())
```

#### Results
- **Caller thread ID**: 12345 (example)
- **Signal thread ID**: 12345 (example)
- **Same thread**: True
- **Consistency across multiple calls**: 100%

#### Conclusion
**Django signals run in the same thread as the caller.**

The caller thread ID and signal thread ID are identical, proving that signal handlers execute in the same thread that triggered the signal. This behavior is consistent across multiple invocations.

**Evidence**:
- Test: `core/tests/test_thread.py::SignalThreadingTests::test_signal_runs_in_same_thread_as_caller`
- API Endpoint: `GET /api/signal/thread/`

---

### Question 3: Do Django signals run in the same database transaction as the caller?

#### Hypothesis
Django signals run in the same database transaction as the caller. Operations performed in signal handlers participate in the caller's transaction.

#### Experiment
1. Started a transaction using `transaction.atomic()`
2. Created a `TransactionTestModel` instance (caller record)
3. The signal handler created another `TransactionTestModel` instance (signal record)
4. Forced a transaction rollback
5. Verified whether both records disappeared

#### Methodology
```python
try:
    with transaction.atomic():
        caller_record = TransactionTestModel.objects.create(
            name="transaction_test",
            created_in_signal=False,
        )
        # Signal creates: signal_record = TransactionTestModel.objects.create(...)
        raise Exception("Force rollback")
except Exception:
    pass

# Check remaining records
remaining = TransactionTestModel.objects.all()
```

#### Results
- **Caller record after rollback**: Not found
- **Signal record after rollback**: Not found
- **Both rolled back**: True
- **Transaction isolation**: Maintained

#### Conclusion
**Django signals run in the same database transaction as the caller.**

When the caller's transaction is rolled back, both the caller's record and the record created in the signal handler are rolled back. This proves that signal operations participate in the same transaction context as the caller.

**Evidence**:
- Test: `core/tests/test_transaction.py::SignalTransactionTests::test_signal_runs_in_same_transaction_on_rollback`
- API Endpoint: `GET /api/signal/transaction/`

---

## Rectangle Class Implementation

### Overview
The `Rectangle` class demonstrates Python's iterator protocol implementation, yielding dictionaries containing length and width dimensions.

### Features
- **Type hints**: Full type annotations for all methods and properties
- **Validation**: Ensures positive integer dimensions
- **Iterator protocol**: Implements `__iter__` and `__next__` methods
- **Mathematical operations**: Area and perimeter calculations
- **Comparison**: Equality and hashing support
- **Immutability**: Dimensions are read-only properties

### Usage Example
```python
from core.rectangle import Rectangle

r = Rectangle(10, 5)

for item in r:
    print(item)

# Output:
# {"length": 10}
# {"width": 5}

# Mathematical operations
print(r.area())        # 50
print(r.perimeter())   # 30
```

### Implementation Details
- The class maintains an internal iteration index
- `__iter__` resets the index and returns `self`
- `__next__` yields dimensions in sequence and raises `StopIteration` when complete
- Dimensions are stored as private attributes with read-only property access
- Comprehensive validation ensures data integrity

### Tests
- Test suite: `core/tests/test_rectangle.py`
- Coverage: Initialization, iteration, edge cases, mathematical operations, comparison, hashing

## Engineering Decisions

### Architecture
- **Separation of Concerns**: Models, signals, views, and business logic are properly separated
- **Clean Architecture**: Core app contains domain logic, with clear boundaries
- **Dependency Injection**: Signal handlers receive instances via Django's signal system

### Testing Strategy
- **Dual Testing Framework**: Both Django TestCase and pytest are supported
- **Comprehensive Coverage**: Tests cover happy paths, edge cases, and error conditions
- **Isolation**: Each test cleans up after itself to ensure independence
- **Evidence-Based**: Tests provide conclusive proof for each hypothesis

### Code Quality
- **Type Hints**: All functions and methods include type annotations
- **Docstrings**: Comprehensive docstrings for all public classes and methods
- **PEP 8 Compliance**: Code follows Python style guidelines
- **Structured Logging**: JSON-formatted logs for production readiness

### Signal Investigation Approach
- **Automated Tests**: All conclusions are backed by automated tests
- **API Endpoints**: RESTful endpoints provide interactive investigation
- **Logging**: Structured logging captures execution details
- **Multiple Methods**: Each question is investigated using multiple approaches for validation

### Performance Considerations
- **Efficient Iteration**: Rectangle class uses minimal overhead for iteration
- **Database Queries**: Tests use in-memory database for speed
- **Signal Optimization**: Signal handlers are designed to be lightweight

## Bonus Exploration

### Additional Signal Investigations

#### Signal Error Propagation
Tests confirm that exceptions raised in signal handlers propagate to the caller, further proving synchronous execution.

#### Multiple Signal Handlers
When multiple signal handlers are registered for the same event, they execute sequentially in the same thread and transaction.

#### Nested Transactions
Signal handlers respect Django's savepoint semantics when used with nested transactions.

### Rectangle Class Extensions

The Rectangle class includes:
- Mathematical operations (area, perimeter)
- Comparison operators (equality, hashing)
- Immutability guarantees
- Comprehensive validation

## Screenshots Placeholder

### API Endpoints
- [ ] Synchronization test response
- [ ] Threading test response
- [ ] Transaction test response

### Test Results
- [x] pytest coverage report
![Test Results](assets/Screenshot%202026-05-31%20191529.png)
- [x] Django test runner output

### Application UI
- [ ] Home page screenshot

## Future Enhancements

### Potential Improvements
1. **Async Signal Support**: Investigate Django's async signal capabilities
2. **Performance Benchmarking**: Add detailed performance metrics
3. **Signal Profiling**: Implement signal execution profiling
4. **Additional Shapes**: Extend to other geometric shapes with iteration
5. **WebSocket Support**: Real-time signal monitoring

### Documentation
1. **API Documentation**: Generate OpenAPI/Swagger documentation
2. **Architecture Diagrams**: Add system architecture visualizations
3. **Video Walkthrough**: Create demonstration video

## Contributing

This project is a demonstration submission. For production use, consider:
- Adding authentication/authorization
- Implementing rate limiting
- Adding comprehensive error handling
- Setting up CI/CD pipelines
- Adding monitoring and alerting

## License

This project is created for educational and demonstration purposes.

## Contact

For questions or feedback about this assignment submission, please refer to the original assignment documentation.

---

**Note**: This project demonstrates professional Django development practices, comprehensive testing, and thorough investigation of Django's signal system. All conclusions are backed by automated tests and API endpoints for interactive verification.
