# ---------------------------------------------------------
# GLOBAL TEST DATABASE
# ---------------------------------------------------------

test_db = InMemoryDBHarness()


# ---------------------------------------------------------
# PYTEST FIXTURES
# ---------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_test_database(monkeypatch):

    test_db.reset()

    # Patch database execution for every service.
    monkeypatch.setattr(
        database,
        "execute_query",
        test_db.mock_execute_query
    )

    # Patch imported execute_query references.
    import services.category_service as category_service
    import services.transaction_service as transaction_service
    import services.budget_service as budget_service
    import services.analytics_service as analytics_service

    monkeypatch.setattr(
        category_service,
        "execute_query",
        test_db.mock_execute_query
    )

    monkeypatch.setattr(
        transaction_service,
        "execute_query",
        test_db.mock_execute_query
    )

    monkeypatch.setattr(
        budget_service,
        "execute_query",
        test_db.mock_execute_query
    )

    monkeypatch.setattr(
        analytics_service,
        "execute_query",
        test_db.mock_execute_query
    )

    # Patch the analysis adapter if it is available.
    try:
        import integrations.analysis_adapter as analysis_adapter

        monkeypatch.setattr(
            analysis_adapter,
            "execute_query",
            test_db.mock_execute_query
        )

    except ImportError:
        pass

    # Prevent tests from connecting to a real MySQL server.
    monkeypatch.setattr(
        database,
        "init_connection_pool",
        lambda *args, **kwargs: None
    )

    monkeypatch.setattr(
        database,
        "test_connection",
        lambda: (True, "Database connection successful")
    )

    try:
        import app as main_app

        monkeypatch.setattr(
            main_app.database,
            "init_connection_pool",
            lambda *args, **kwargs: None
        )

        monkeypatch.setattr(
            main_app.database,
            "test_connection",
            lambda: (True, "Database connection successful")
        )

    except ImportError:
        pass

    yield


@pytest.fixture
def app():
    application = create_app(TestingConfig)

    application.config.update({
        "TESTING": True,
        "PROPAGATE_EXCEPTIONS": False,
    })

    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def database_mock():
    return test_db