from dataclasses import dataclass, field


@dataclass(frozen=True)
class SqliteSettings:
    """The database and the clients of the SQLite demo backend. The names are the keys of the configuration (config/README.md).

    `rpp_sqlite_url` is a SQLAlchemy URL: a file (`sqlite:///demo.db`) or, by default, a database in memory
    (`sqlite://`). `rpp_sqlite_clients` maps each client (the user of the Basic authentication, and the sponsor id of
    what it creates) to the hash of its password, a `scrypt$...` string (`python -m registry_adapter.sqlite.hash_password`).
    The hash is a credential: it is never logged.
    """
    rpp_sqlite_url: str = "sqlite://"
    rpp_sqlite_clients: dict = field(default_factory=dict, repr=False)

    def __post_init__(self):
        clients = self.rpp_sqlite_clients
        if not isinstance(clients, dict) or not all(
                isinstance(user, str) and user and isinstance(hashed, str) and hashed for user, hashed in clients.items()):
            raise ValueError("rpp_sqlite_clients maps each user to the hash of its password")
